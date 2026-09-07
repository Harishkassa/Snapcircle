from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig

if GlobalHydra.instance().is_initialized():
    GlobalHydra.instance().clear()

with initialize(config_path="../../config", version_base=None):
    cfg: DictConfig = compose(config_name="face_capture")

MIN_SHARPNESS = cfg.face_params.MIN_SHARPNESS
MIN_CONFIDENCE = cfg.face_params.MIN_CONFIDENCE
LOCK_FRAMES_REQUIRED = cfg.face_params.LOCK_FRAMES_REQUIRED
MIN_FACE_RATIO = cfg.face_params.MIN_FACE_RATIO
MAX_DETECTION_DIM = cfg.face_params.MAX_DETECTION_DIM
SAVE_DIR = cfg.face_params.SAVE_DIR
FACE_TTL_SECONDS = cfg.face_params.FACE_TTL_SECONDS
MATCH_THRESHOLD = cfg.face_params.MATCH_THRESHOLD