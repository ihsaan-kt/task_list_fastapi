## Sample FastAPI implementation with authentication

- run `fastapi dev main.py` to deploy api locally.
- Test API functionality with `http://127.0.0.1:8000/docs`.
- API endpoints uses JWT for authentication and authorization;
  - Input `username` and `password` (`john.doe`:`secure_password`) in `\token` endpoint to obtain Bearer token.
  - Input `username`, `password` and Bearer token under `client_secret` in `Authorization`.

## to run in Docker
  - `docker build -t fastapi_image .`
  - `docker run -d --name fastapi_docker -p 80:80 fastapi_image`
  - should be able to test API locally as before with `http://127.0.0.1:8000/docs`.

### thank you for your time and consideration. Really look forward to working with you. 
