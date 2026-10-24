<template>
  <main class="container">
    <header>
      <h1>🐾 Pet & Owner Manager</h1>
      <p>AWS Hybrid CI/CD Demo Application (FastAPI + Vue.js)</p>
    </header>

    <div class="grid">
      <!-- Owner Form -->
      <section>
        <h3>Add Owner</h3>
        <form @submit.prevent="addOwner">
          <input v-model="newOwner.name" placeholder="Full Name" required />
          <input v-model="newOwner.email" type="email" placeholder="Email Address" required />
          <input v-model="newOwner.phone" placeholder="Phone Number" />
          <button type="submit">Save Owner</button>
        </form>
      </section>

      <!-- Pet Form -->
      <section>
        <h3>Add Pet</h3>
        <form @submit.prevent="addPet">
          <input v-model="newPet.name" placeholder="Pet Name" required />
          <input v-model="newPet.species" placeholder="Species (Dog, Cat, etc.)" required />
          <input v-model="newPet.breed" placeholder="Breed" />
          <select v-model="newPet.owner_id" required>
            <option value="" disabled selected>Select Owner</option>
            <option v-for="owner in owners" :key="owner.id" :value="owner.id">
              {{ owner.name }}
            </option>
          </select>
          <button type="submit" :disabled="!owners.length">Save Pet</button>
        </form>
      </section>
    </div>

    <hr />

    <!-- Owners List -->
    <section>
      <h3>Registered Owners & Pets</h3>
      <div v-if="!owners.length"><em>No owners registered yet.</em></div>
      <article v-for="owner in owners" :key="owner.id">
        <header>
          <strong>{{ owner.name }}</strong> ({{ owner.email }})
          <button class="outline secondary" style="float: right; padding: 2px 8px;" @click="deleteOwner(owner.id)">Delete</button>
        </header>
        <p><strong>Phone:</strong> {{ owner.phone || 'N/A' }}</p>
        <p><strong>Pets:</strong></p>
        <ul>
          <li v-for="pet in getPetsForOwner(owner.id)" :key="pet.id">
            {{ pet.name }} ({{ pet.species }} - {{ pet.breed || 'Unknown' }})
            <a href="#" @click.prevent="deletePet(pet.id)" style="color: red; margin-left: 10px;">Remove</a>
          </li>
          <li v-if="!getPetsForOwner(owner.id).length"><em>No pets registered for this owner.</em></li>
        </ul>
      </article>
    </section>
  </main>
</template>

<script>
export default {
  data() {
    return {
      owners: [],
      pets: [],
      newOwner: { name: '', email: '', phone: '' },
      newPet: { name: '', species: '', breed: '', owner_id: '' }
    }
  },
  mounted() {
    this.loadFromLocalStorage()
  },
  methods: {
    saveToLocalStorage() {
      localStorage.setItem('aws_demo_owners', JSON.stringify(this.owners))
      localStorage.setItem('aws_demo_pets', JSON.stringify(this.pets))
    },
    loadFromLocalStorage() {
      const savedOwners = localStorage.getItem('aws_demo_owners')
      const savedPets = localStorage.getItem('aws_demo_pets')
      if (savedOwners) this.owners = JSON.parse(savedOwners)
      if (savedPets) this.pets = JSON.parse(savedPets)
    },
    addOwner() {
      const owner = {
        id: Date.now(),
        ...this.newOwner
      }
      this.owners.push(owner)
      this.saveToLocalStorage()
      this.newOwner = { name: '', email: '', phone: '' }
    },
    addPet() {
      const pet = {
        id: Date.now(),
        ...this.newPet
      }
      this.pets.push(pet)
      this.saveToLocalStorage()
      this.newPet = { name: '', species: '', breed: '', owner_id: '' }
    },
    deleteOwner(ownerId) {
      this.owners = this.owners.filter(o => o.id !== ownerId)
      this.pets = this.pets.filter(p => p.owner_id !== ownerId)
      this.saveToLocalStorage()
    },
    deletePet(petId) {
      this.pets = this.pets.filter(p => p.id !== petId)
      this.saveToLocalStorage()
    },
    getPetsForOwner(ownerId) {
      return this.pets.filter(p => p.owner_id === ownerId)
    }
  }
}
</script>