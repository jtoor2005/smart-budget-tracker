// First, create a new Vue project
// npm create vue@latest expense-tracker
// cd expense-tracker
// npm install axios

// src/App.vue
<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-6">Expense Tracker</h1>
    
    <!-- Expense Form -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-6">
      <h2 class="text-xl font-semibold mb-4">Add New Expense</h2>
      <div class="mb-4">
        <label class="block text-gray-700 mb-2" for="description">Description</label>
        <input 
          v-model="newExpense.description" 
          id="description"
          class="w-full p-2 border border-gray-300 rounded" 
          type="text" 
          placeholder="What did you spend on?"
        />
      </div>
      <div class="mb-4">
        <label class="block text-gray-700 mb-2" for="amount">Amount</label>
        <input 
          v-model="newExpense.amount" 
          id="amount"
          class="w-full p-2 border border-gray-300 rounded" 
          type="number" 
          step="0.01" 
          placeholder="How much did you spend?"
        />
      </div>
      <button 
        @click="addExpense" 
        class="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
        :disabled="isSubmitting"
      >
        {{ isSubmitting ? 'Adding...' : 'Add Expense' }}
      </button>
    </div>
    
    <!-- Expenses List -->
    <div class="bg-white p-6 rounded-lg shadow-md">
      <h2 class="text-xl font-semibold mb-4">Your Expenses</h2>
      <div v-if="isLoading" class="text-center py-4">
        Loading expenses...
      </div>
      <div v-else-if="expenses.length === 0" class="text-center py-4 text-gray-500">
        No expenses yet. Add one above!
      </div>
      <table v-else class="w-full border-collapse">
        <thead>
          <tr class="bg-gray-100">
            <th class="text-left p-2 border">Description</th>
            <th class="text-left p-2 border">Amount</th>
            <th class="text-left p-2 border">Category</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(expense, index) in expenses" :key="index" class="border-b">
            <td class="p-2 border">{{ expense.description }}</td>
            <td class="p-2 border">${{ expense.amount.toFixed(2) }}</td>
            <td class="p-2 border">
              <span class="px-2 py-1 rounded-full text-sm" :class="getCategoryColor(expense.category)">
                {{ expense.category }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// Configure the base URL for your API
// In development, you might proxy requests or use the full URL
const API_URL = 'http://localhost:8000'; // Change this to your deployed API URL in production

export default {
  data() {
    return {
      newExpense: {
        description: '',
        amount: ''
      },
      expenses: [],
      isLoading: false,
      isSubmitting: false,
      error: null
    }
  },
  mounted() {
    this.fetchExpenses();
  },
  methods: {
    async fetchExpenses() {
      this.isLoading = true;
      try {
        const response = await axios.get(`${API_URL}/expenses/`);
        this.expenses = response.data;
      } catch (error) {
        console.error('Error fetching expenses:', error);
        this.error = 'Failed to load expenses. Please try again.';
      } finally {
        this.isLoading = false;
      }
    },
    async addExpense() {
      if (!this.newExpense.description || !this.newExpense.amount) {
        alert('Please fill out both description and amount');
        return;
      }

      this.isSubmitting = true;
      try {
        const response = await axios.post(`${API_URL}/add_expense/`, {
          description: this.newExpense.description,
          amount: parseFloat(this.newExpense.amount)
        });
        
        // Add the new expense to the expenses array
        this.expenses.unshift(response.data);
        
        // Reset the form
        this.newExpense.description = '';
        this.newExpense.amount = '';
        
      } catch (error) {
        console.error('Error adding expense:', error);
        alert('Failed to add expense. Please try again.');
      } finally {
        this.isSubmitting = false;
      }
    },
    getCategoryColor(category) {
      const categoryColors = {
        'Food': 'bg-green-100 text-green-800',
        'Shopping': 'bg-blue-100 text-blue-800',
        'Furniture': 'bg-orange-100 text-orange-800',
        'Transportation': 'bg-purple-100 text-purple-800',
        'Entertainment': 'bg-pink-100 text-pink-800',
        'Utilities': 'bg-yellow-100 text-yellow-800',
        'Housing': 'bg-indigo-100 text-indigo-800',
        'Healthcare': 'bg-red-100 text-red-800'
      };
      
      return categoryColors[category] || 'bg-gray-100 text-gray-800';
    }
  }
}
</script>

// main.js
import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css' // Tailwind CSS

createApp(App).mount('#app')

// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Proxy API requests to your FastAPI backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})