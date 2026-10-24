from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app import database
from app.models import Owner, Pet

app = FastAPI(
    title="Pet & Owner Management API",
    description="RESTful API for the AWS Hybrid CI/CD Demo",
    version="1.0.0"
)

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy", "service": "Pet & Owner API"}

# --- OWNER ENDPOINTS ---
@app.get("/owners", response_model=List[Owner])
def list_owners():
    return database.owners

@app.post("/owners", response_model=Owner, status_code=status.HTTP_201_CREATED)
def create_owner(owner: Owner):
    owner.id = len(database.owners) + 1
    database.owners.append(owner)
    return owner

@app.delete("/owners/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner(owner_id: int):
    database.owners[:] = [owner for owner in database.owners if owner.id != owner_id]
    database.pets[:] = [pet for pet in database.pets if pet.owner_id != owner_id]
    return None

# --- PET ENDPOINTS ---
@app.get("/pets", response_model=List[Pet])
def list_pets():
    return database.pets

@app.post("/pets", response_model=Pet, status_code=status.HTTP_201_CREATED)
def create_pet(pet: Pet):
    # Validate owner exists
    if not any(owner.id == pet.owner_id for owner in database.owners):
        raise HTTPException(status_code=404, detail="Owner not found")
    
    pet.id = len(database.pets) + 1
    database.pets.append(pet)
    return pet

@app.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(pet_id: int):
    database.pets[:] = [pet for pet in database.pets if pet.id != pet_id]
    return None