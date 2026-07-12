# Docker guide

This project includes a Docker configuration for running the Streamlit application with the committed demo dataset.

## Build the image

From the project root:

```bash
docker build -t telecom-customer-intelligence .
```
## Run the app
```text
docker run --rm -p 8501:8501 telecom-customer-intelligence
```
Open:
```text
http://localhost:8501
```
## Data behavior
The Docker image includes the committed demo files from:
```text
data/demo/
```
The full local generated datasets under data/processed/ are intentionally excluded from the image.

## Notes

- The container runs the Streamlit app only.
- Transformer/BERT inference is not run inside the container.
- NLP outputs are precomputed and stored in the committed demo files.