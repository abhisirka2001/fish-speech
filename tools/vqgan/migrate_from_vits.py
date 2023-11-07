import hydra
import torch
from loguru import logger
from omegaconf import DictConfig, OmegaConf

# register eval resolver
OmegaConf.register_new_resolver("eval", eval)


@hydra.main(
    version_base="1.3",
    config_path="../../fish_speech/configs",
    config_name="hubert_vq.yaml",
)
def main(cfg: DictConfig):
    generator_ckpt = cfg.get(
        "generator_ckpt", "results/hubert-vq-pretrain/rcell/G_23000.pth"
    )
    discriminator_ckpt = cfg.get(
        "discriminator_ckpt", "results/hubert-vq-pretrain/rcell/D_23000.pth"
    )
    model = hydra.utils.instantiate(cfg.model)

    # Generator
    logger.info(f"Model loaded, restoring from {generator_ckpt}")
    generator_weights = torch.load(generator_ckpt, map_location="cpu")["model"]

    # Decoder
    generator_state = {
        k[4:]: v
        for k, v in generator_weights.items()
        if k.startswith("dec.") and not k.startswith("dec.cond.")
    }
    logger.info(f"Found {len(generator_state)} HiFiGAN weights, restoring...")
    r = model.generator.dec.load_state_dict(generator_state, strict=False)
    logger.info(f"Generator weights restored. {r}")

    # Posterior Encoder
    # encoder_state = {
    #     k[6:]: v
    #     for k, v in generator_weights.items()
    #     if k.startswith("enc_q.") and not k.startswith("enc_q.proj.")
    # }
    # logger.info(f"Found {len(encoder_state)} posterior encoder weights, restoring...")
    # x = model.generator.enc_q.load_state_dict(encoder_state, strict=False)
    # logger.info(f"Posterior encoder weights restored. {x}")

    # Flow
    # flow_state = {
    #     k[5:]: v for k, v in generator_weights.items() if k.startswith("flow.")
    # }
    # logger.info(f"Found {len(flow_state)} flow weights, restoring...")
    # model.flow.load_state_dict(flow_state, strict=True)
    # logger.info("Flow weights restored.")

    # Discriminator
    logger.info(f"Model loaded, restoring from {discriminator_ckpt}")
    discriminator_weights = torch.load(discriminator_ckpt, map_location="cpu")["model"]
    logger.info(
        f"Found {len(discriminator_weights)} discriminator weights, restoring..."
    )
    model.discriminator.load_state_dict(discriminator_weights, strict=True)
    logger.info("Discriminator weights restored.")

    torch.save(model.state_dict(), cfg.ckpt_path)
    logger.info("Done")


if __name__ == "__main__":
    main()