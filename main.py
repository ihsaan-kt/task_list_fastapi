from enum import IntEnum
from typing import Optional
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import pandas as pd
import pandera as pa
from pandera.typing import Series

from .auth import User, Token, authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from apitally.fastapi import ApitallyMiddleware


api = FastAPI()
api.add_middleware(
    ApitallyMiddleware,
    client_id="client_id_given_in_apitally_account",
)

class Priority(IntEnum):
    """
    Enumerating task priority.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class taskBase(BaseModel):
    """
    Task model requiring name, description, priority.
    """
    task_name: str        = Field(..., min_length=3, max_length= 256, description="Name of To-Do List")
    task_description: str = Field(..., description="Description of To-Do List")
    priority: Priority    = Field(default=Priority.LOW, description="Priority of Task")

class Task(taskBase):
    """
    Base task model only requiring task_id.
    """
    task_id: int = Field(..., description="Unique Identifier of Task")

class taskCreate(taskBase):
    """
    Flexible model for POST endpoint.
    """
    pass

class taskUpdate(BaseModel):
    """
    Model for PUT with optional fields.
    """
    task_name: Optional[str]        = Field(None, min_length=3, max_length= 256, description="Name of To-Do List")
    task_description: Optional[str] = Field(None, description="Description of To-Do List")
    priority: Optional[Priority]    = Field(None, description="Priority of Task")

# Pandera schema for validating tasks
class TaskSchema(pa.DataFrameModel):
    task_id: Series[int] = pa.Field(ge=1)
    task_name: Series[str] = pa.Field(str_length={"min_value": 3, "max_value": 256})
    task_description: Series[str]
    priority: Series[int] = pa.Field(isin=[1, 2, 3])

    class Config:
        strict = True

# mock task DB
all_tasks = [
    Task(task_id=1, task_name="Health", task_description="get some sunlight", priority=Priority.HIGH),
    Task(task_id=2, task_name="Work", task_description="apply for jobs", priority=Priority.HIGH),
    Task(task_id=3, task_name="Study", task_description="practice k8s", priority=Priority.MEDIUM),
    Task(task_id=4, task_name="Read", task_description="read a chapter", priority=Priority.LOW),
    Task(task_id=5, task_name="Food", task_description="get groceries", priority=Priority.LOW)
]

def get_tasks_dataframe():
    data = [{'task_id': task.task_id, 'task_name': task.task_name,
             'task_description': task.task_description, 'priority': task.priority.value}
            for task in all_tasks]
    return pd.DataFrame(data)

@api.get("/")
async def read_root():
    return {"message": "Hello from FastAPI in Docker!"}

# Authentication
@api.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for users to log in and obtain an access token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# GET single task
@api.get('/tasks/{task_id}', response_model=Task)
async def get_task(task_id: int, current_user: User = Depends(get_current_user)):
    """
    Retrieves a single task by its ID.
    """
    print(f"Authenticated user for get_task: {current_user.username}")

    tasks_df = get_tasks_dataframe()
    task = tasks_df[tasks_df['task_id'] == task_id]

    if task.empty:
        raise HTTPException(status_code=404, detail='Task ID Not Found')

    task_series = task.iloc[0]
    return Task(**task_series.to_dict())

# GET all tasks
@api.get('/tasks')
async def get_all_tasks(current_user: User = Depends(get_current_user)):
    """
    Retrieves all tasks.
    """
    print(f"Authenticated user for get_all_tasks: {current_user.username}")
    tasks_df = get_tasks_dataframe()
    return tasks_df.to_dict(orient='records')

# POST
@api.post('/tasks', response_model=Task)
async def create_task(task: taskCreate, current_user: User = Depends(get_current_user)):
    """
    Creates a new task.
    """
    print(f"Authenticated user for create_task: {current_user.username}")

    new_task_id = max(t.task_id for t in all_tasks) + 1 if all_tasks else 1

    # Create a new task using pandera validated data
    new_task_data = {
        "task_id": new_task_id,
        "task_name": task.task_name,
        "task_description": task.task_description,
        "priority": task.priority.value
    }

    # Validate new task using pandera
    TaskSchema.validate(new_task_data)

    new_task = Task(task_id=new_task_data["task_id"],
                    task_name=new_task_data["task_name"],
                    task_description=new_task_data["task_description"],
                    priority=Priority(new_task_data["priority"]))

    all_tasks.append(new_task)

    return new_task

# PUT
@api.put('/tasks/{task_id}', response_model=Task)
async def update_task(task_id: int, updated_task: taskUpdate, current_user: User = Depends(get_current_user)):
    """
    Updates an existing task by its ID.
    """
    print(f"Authenticated user for update_task: {current_user.username}")

    tasks_df = get_tasks_dataframe()

    if task_id not in tasks_df['task_id'].values:
        raise HTTPException(status_code=404, detail='Task ID Not Found')

    for task in all_tasks:
        if task.task_id == task_id:
            if updated_task.task_name is not None:
                task.task_name = updated_task.task_name
            if updated_task.task_description is not None:
                task.task_description = updated_task.task_description
            if updated_task.priority is not None:
                task.priority = updated_task.priority
            break

    updated_task_data = {
        "task_id": task_id,
        "task_name": task.task_name,
        "task_description": task.task_description,
        "priority": task.priority.value
    }

    # Validate updated task using pandera
    TaskSchema.validate(updated_task_data)

    return task

# DELETE
@api.delete('/tasks/{task_id}')
async def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    """
    Deletes a task by its ID.
    """
    print(f"Authenticated user for delete_task: {current_user.username}")

    tasks_df = get_tasks_dataframe()

    if task_id not in tasks_df['task_id'].values:
        raise HTTPException(status_code=404, detail='Task ID Not Found')

    for n, task in enumerate(all_tasks):
        if task.task_id == task_id:
            deleted_task = all_tasks.pop(n)
            return deleted_task

    raise HTTPException(status_code=404, detail='Task ID Not Found')
