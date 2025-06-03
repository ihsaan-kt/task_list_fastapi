## Sample FastAPI implementation with JWT

## Deploying locally:
  ```
  fastapi dev main.py
  ```
- Test API functionality in browser with `http://127.0.0.1:8000/docs`.
- API endpoints uses JWT for authentication and authorization;
  - Input `username` and `password` (`john.doe`:`secure_password`) in `\token` endpoint to obtain Bearer token.
  - Input `username`, `password` and Bearer token under `client_secret` in `Authorization`.

## Deploying in Docker
```
  docker build -t fastapi_image
  docker run -d --name fastapi_docker -p 80:80 fastapi_image
```
  - should be able to test API in browser as before with `http://127.0.0.1:8000/docs`.

- `/tests` hold pytest functions for `auth.py`.
- to run pytests:
  ```
  cd /tests
  pytest 
  ```
  

### Thank you for your time and consideration. 
