# Python Flask API Template

This is a template repository for a Python Flask microservice. To use this:

1. Create a repo using this template
2. Run `./replace-with-service-name.sh YOUR_DESIRED_SERVICE_NAME` to update the service name in all files
3. Delete `./replace-with-service-name.sh`
4. Update this README
5. Update `.github/CODEOWNERS` to point to the service owners

## Set-up

- Download the repo
- Add pre-commit hook for formatting: `cp ci/git/pre-commit .git/hooks/pre-commit`

## Local Development

After running the service with Python or Docker, you can access it by running `curl localhost:8080/`.

**Note:** Ensure you are authenticated to pull Docker images from the private registry.

```shell
gcloud auth login
```

### Python

```
pip install -r requirements.txt
python main.py
```

### Docker

```
docker build -f ci/Dockerfile -t flask-api .
docker run -p 8080:8080 flask-api
```

## Linting and Formatting

- Lint: `ci/lint.sh`
- Format: `black .`

## Testing

- Run tests: `ci/tests.sh`
