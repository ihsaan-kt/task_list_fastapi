# task_list_fastapi

Sample fastapi implementation with authentication

- run `fastapi dev main.py` to deploy api locally.

- should be able to test API functionality with `http://127.0.0.1:8000/docs`.

- API uses JWT for authentication and authorization.
- Input `username` and `password` (`john.doe`:`secure_password`) in `\token` API to obtain Bearer token.
- Input `username`, `password` and Bearer token under `client_secret` in `Authorization`.
