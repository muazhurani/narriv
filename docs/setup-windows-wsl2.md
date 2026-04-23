# Windows + WSL2 setup

The lowest-friction setup so far is:

- Run API and frontend where you prefer.
- Run the Tribe worker in WSL2 Ubuntu.

Worker setup inside WSL2:

1. Install Python 3.11 and `ffmpeg`.
2. Clone TribeV2 and install it in a dedicated venv.
3. Authenticate Hugging Face (`huggingface-cli login`) for gated model dependencies.
4. Set `TRIBE_REPO_PATH` to the path visible to the worker process.

For a native Windows worker, set `TRIBE_REPO_PATH` to your local TribeV2 clone:

- `TRIBE_REPO_PATH=<path-to-your-tribev2-clone>`
