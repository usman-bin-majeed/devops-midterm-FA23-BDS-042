# CSC418 Lab Midterm — Auto-Retraining ML Pipeline (FA23-BDS-042)

A push of new data to this repository triggers Jenkins (GitHub webhook), which
retrains the model, runs the tests, builds a Docker image, redeploys the
FastAPI service on AWS EC2 and emails the result.

| Item | Value |
|---|---|
| Student Reg No | FA23-BDS-042 |
| Scenario | warehouse (`config.json`, variant `outliers`) |
| Jenkins job | `MIDTERM-FA23-BDS-042` |
| Live API | http://13.62.195.247:8000/metrics |
| Docker image | `usman15274/midterm-fa23-bds-042` |

## Pipeline (`Jenkinsfile`)

1. **Fetch latest data** – checkout; `scripts/merge_data.py` folds any extra CSV in `dataset/` into `dataset/train.csv`.
2. **Snapshot current model** – saves the live `/metrics` to compare accuracy.
3. **Retrain & test** – Docker `train` stage runs `train.py` then `pytest tests/`.
4. **Build image** – slim runtime image containing the new model; writes the old-vs-new accuracy report.
5. **Deploy to EC2** – replaces the `midterm-api` container on port 8000.
6. **Verify deployment** – checks the live endpoint serves the new `model_version`.
7. **Push to Docker Hub** – `:BUILD_NUMBER` and `:latest`.
8. **Email** (post, always) – to the instructor, subject contains the Reg No, includes the accuracy comparison.

## Endpoints

- `GET /metrics` → `student_id, accuracy, training_rows, model_version, git_sha`
- `POST /predict` → body `{"records": [{"queue_depth": 0.1, "staff_gap": 0.2, "truck_delay": 0.3, "order_burst": 0.4}]}`
- `GET /health`

## Regenerate the initial dataset

```bash
python generate_dataset.py --config config.json --output dataset/train.csv --rows 300
```
