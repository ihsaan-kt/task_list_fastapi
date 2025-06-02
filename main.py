from enum import IntEnum
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


api = FastAPI()


class Priority(IntEnum):
  LOW = 1
  MEDIUM = 2
  HIGH = 3


class taskBase(BaseModel):
  task_name: str = Field(..., min_length=3, max_length= 256, description="Name of To-Do List")
  task_description: str = Field(..., description="Description of To-Do List")
  priority: Priority = Field(default=Priority.LOW, description="Priority of Task")


class Task(taskBase):
  task_id: int = Field(..., description="Unique Identifier of Task")


class taskCreate(taskBase):
  pass


class taskUpdate(BaseModel):
  task_name: Optional[str] = Field(None, min_length=3, max_length= 256, description="Name of To-Do List")
  task_description: Optional[str] = Field(None, description="Description of To-Do List")
  priority: Optional[Priority] = Field(None, description="Priority of Task")


all_tasks = [
  Task(task_id=1, task_name="Health", task_description="get some sunlight", priority=Priority.HIGH),
  Task(task_id=2, task_name="Work", task_description="apply for jobs", priority=Priority.HIGH),
  Task(task_id=3, task_name="Study", task_description="practice k8s", priority=Priority.MEDIUM),
  Task(task_id=4, task_name="Read", task_description="read a chapter", priority=Priority.LOW),
  Task(task_id=5, task_name="Food", task_description="get groceries", priority=Priority.LOW)
]

# GET
@api.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int):
  for task in all_tasks:
    if task.task_id is task_id:
      return task
  
  raise HTTPException(status_code=404, detail='Task ID Not Found')


# GET all tasks
@api.get('/tasks')
def get_all_tasks():
  return all_tasks


# POST
@api.post('/tasks', response_model=Task)
def create_task(task: taskCreate):
  new_task_id = max(task.task_id for task in all_tasks) + 1
  
  new_task = Task(task_id = new_task_id,
                  task_name = task.task_name,
                  task_description = task.task_description,
                  priority = task.priority)
  
  all_tasks.append(new_task)
  
  return new_task


# PUT
@api.put('/tasks/{task_id}', response_model=Task)
def update_task(task_id: int, updated_task: taskUpdate):
  for task in all_tasks:
    if task.task_id is task_id:
      task.task_name = updated_task.task_name
      task.task_description = updated_task.task_description
    
      return task

raise HTTPException(status_code=404, detail='Task ID Not Found')


# DELETE
@api.delete('/tasks/{task_id}')
def delete_task(task_id: int):
  for n, task in enumerate(all_tasks):
    if task.task_id is task_id:
      deleted_task = all_tasks.pop(n)
    return deleted_task

  raise HTTPException(status_code=404, detail='Task ID Not Found')
  
