"""
tune_thresholds.py

Standalone Hydra script to evaluate the face-detection pipeline
(detection + size + sharpness thresholds) against a folder of sample
test images. Not connected to FastAPI/uvicorn -- pure offline evaluation.

Run:
    python tune_thresholds.py

Sweep multiple threshold combinations:
    python tune_thresholds.py --multirun \
        face_params.MIN_SHARPNESS=10,15,20 \
        face_params.MIN_CONFIDENCE=0.85,0.90,0.95
"""
from scripts import *

logger = logging.getLogger(__name__)

# Folder containing your sample test images
TEST_IMAGES_DIR = "test_images"
SAVE_DIR = "eval_captured_faces"


# ---------------------------------------------------------------------------
# Pipeline helper functions (same logic as your live-capture pipeline)
# ---------------------------------------------------------------------------
def resize_frame(frame, max_dim: int = 640):
    h, w = frame.shape[:2]
    scale = max_dim / max(h, w)
    if scale < 1:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    return frame


def select_largest_face(faces: dict, min_confidence: float):
    if not faces or not isinstance(faces, dict):
        return None
    best, best_area = None, 0
    for f in faces.values():
        x1, y1, x2, y2 = f["facial_area"]
        area = (x2 - x1) * (y2 - y1)
        if area > best_area and f["score"] >= min_confidence:
            best_area = area
            best = f
    return best


def is_face_big_enough(face: dict, frame_shape, min_face_ratio: float) -> bool:
    x1, y1, x2, y2 = face["facial_area"]
    face_h = y2 - y1
    frame_h = frame_shape[0]
    return (face_h / frame_h) >= min_face_ratio


def crop_face(frame, face: dict, margin: float = 0.3):
    x1, y1, x2, y2 = face["facial_area"]
    w, h = x2 - x1, y2 - y1
    mx, my = int(w * margin), int(h * margin)
    x1, y1 = max(0, x1 - mx), max(0, y1 - my)
    x2, y2 = min(frame.shape[1], x2 + mx), min(frame.shape[0], y2 + my)
    return frame[y1:y2, x1:x2]


def sharpness_score(img) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# ---------------------------------------------------------------------------
# Evaluation over a folder of test images
# ---------------------------------------------------------------------------
def evaluate_pipeline(cfg: DictConfig) -> dict:
    p = cfg.face_params

    results = {
        "total_images": 0,
        "no_face": 0,
        "no_confident_face": 0,
        "too_small": 0,
        "too_blurry": 0,
        "good_frames": 0,
        "saved_files": [],
    }

    if not os.path.isdir(TEST_IMAGES_DIR):
        logger.warning(f"Test images folder not found: {TEST_IMAGES_DIR}")
        return results

    os.makedirs(SAVE_DIR, exist_ok=True)

    image_files = [
        f for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    good_frame_count = 0
    best_frame = None
    best_sharpness = -1

    for filename in image_files:
        results["total_images"] += 1
        img_path = os.path.join(TEST_IMAGES_DIR, filename)

        # ---- 1. Decode (read from disk here; same idea as decode_frame) ----
        frame = cv2.imread(img_path)
        if frame is None:
            logger.warning(f"Could not decode: {filename}")
            continue

        # ---- 2. Resize ----
        frame = resize_frame(frame, max_dim=p.MAX_DETECTION_DIM)

        # ---- 3. Detect faces ----
        faces = RetinaFace.detect_faces(frame)
        if not isinstance(faces, dict) or not faces:
            results["no_face"] += 1
            good_frame_count = 0
            logger.info(f"{filename}: NO FACE")
            continue

        # ---- 4. Select largest confident face ----
        face = select_largest_face(faces, p.MIN_CONFIDENCE)
        if face is None:
            results["no_confident_face"] += 1
            good_frame_count = 0
            logger.info(f"{filename}: NO CONFIDENT FACE")
            continue

        # ---- 5. Size check ----
        if not is_face_big_enough(face, frame.shape, p.MIN_FACE_RATIO):
            results["too_small"] += 1
            good_frame_count = 0
            logger.info(f"{filename}: TOO SMALL (face_ratio below {p.MIN_FACE_RATIO})")
            continue

        # ---- 6. Crop + sharpness check ----
        face_crop = crop_face(frame, face)
        sharp = sharpness_score(face_crop)

        if sharp < p.MIN_SHARPNESS:
            results["too_blurry"] += 1
            good_frame_count = 0
            logger.info(f"{filename}: TOO BLURRY (sharpness={sharp:.2f} < {p.MIN_SHARPNESS})")
            continue

        # ---- 7. Good frame -- update streak + best frame ----
        good_frame_count += 1
        results["good_frames"] += 1
        if sharp > best_sharpness:
            best_sharpness = sharp
            best_frame = face_crop.copy()

        logger.info(
            f"{filename}: GOOD (score={face['score']:.2f}, sharpness={sharp:.2f}, "
            f"streak={good_frame_count}/{p.LOCK_FRAMES_REQUIRED})"
        )

        # ---- 8. Lock + save once streak target reached ----
        if good_frame_count >= p.LOCK_FRAMES_REQUIRED:
            save_path = os.path.join(SAVE_DIR, f"locked_{int(time.time())}_{filename}")
            cv2.imwrite(save_path, best_frame)
            results["saved_files"].append(save_path)
            logger.info(f"LOCKED & SAVED: {save_path}")
            good_frame_count = 0
            best_frame, best_sharpness = None, -1

    return results


@hydra.main(config_path="../config", config_name="face_capture", version_base=None)
def run_experiment(cfg: DictConfig):
    logger.info(
        f"Testing with: MIN_SHARPNESS={cfg.face_params.MIN_SHARPNESS}, "
        f"MIN_CONFIDENCE={cfg.face_params.MIN_CONFIDENCE}, "
        f"MIN_FACE_RATIO={cfg.face_params.MIN_FACE_RATIO}, "
        f"LOCK_FRAMES_REQUIRED={cfg.face_params.LOCK_FRAMES_REQUIRED}"
    )

    results = evaluate_pipeline(cfg)

    logger.info("---- SUMMARY ----")
    for k, v in results.items():
        logger.info(f"{k}: {v}")


if __name__ == "__main__":
    run_experiment()