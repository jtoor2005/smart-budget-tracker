<template>
  <div class="expense-tracker">
    <nav class="navbar">
      <div class="container">
        <h1 class="app-title">Smart Expense Tracker</h1>
      </div>
    </nav>
    
    <div class="main-container">
      <!-- CSV Import Component -->
      <CsvImport @import-complete="fetchExpenses" class="csv-import-wrapper" />
      
      <div class="content-grid">
        <!-- Left Column -->
        <div class="form-column">
          <div class="card">
            <h2 class="card-title">Add New Expense</h2>
            <div class="form-group">
              <label class="form-label" for="description">Description</label>
              <input 
                v-model="newExpense.description" 
                id="description"
                class="form-input" 
                type="text" 
                placeholder="What did you spend on?"
              />
            </div>
            <div class="form-group">
              <label class="form-label" for="amount">Amount</label>
              <div class="amount-input-container">
                <span class="currency-symbol">$</span>
                <input 
                  v-model="newExpense.amount" 
                  id="amount"
                  class="form-input amount-input" 
                  type="number" 
                  step="0.01" 
                  placeholder="0.00"
                />
              </div>
            </div>
            <button 
              @click="addExpense" 
              class="submit-button"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? 'Adding...' : 'Add Expense' }}
            </button>
          </div>
          
          <!-- Budget Tracker Component -->
          <BudgetTracker :expenses="expenses" class="budget-tracker-wrapper" />
        </div>
        
        <!-- Expenses List Column -->
        <div class="list-column">
          <div class="card">
            <div class="expenses-header">
              <h2 class="card-title">Your Expenses</h2>
              <span class="expense-count" :class="{ 'expense-count-changed': expenseCountChanged }">
                {{ expenses.length }} {{ expenses.length === 1 ? 'Expense' : 'Expenses' }}
              </span>
            </div>
            
            <div v-if="isLoading" class="loading-container">
              <div class="spinner"></div>
              <p class="loading-text">Loading expenses...</p>
            </div>
            
            <div v-else-if="expenses.length === 0" class="empty-state">
              <svg class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
              </svg>
              <p class="empty-text">No expenses yet. Add one to get started!</p>
            </div>
            
            <div v-else class="expense-table-container">
              <table class="expense-table">
                <thead>
                  <tr>
                    <th class="table-header description-header">Description</th>
                    <th class="table-header amount-header">Amount</th>
                    <th class="table-header category-header">Category</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(expense, index) in expenses" :key="index" class="expense-row">
                    <td class="description-cell">{{ expense.description }}</td>
                    <td class="amount-cell">${{ expense.amount.toFixed(2) }}</td>
                    <td class="category-cell">
                      <span class="category-badge" :class="'category-' + expense.category.toLowerCase().replace(' ', '-')">
                        {{ expense.category }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div class="total-amount">
                Total: ${{ getTotalAmount() }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <footer class="footer">
      <div class="container">
        <p class="footer-text">Smart Expense Tracker © {{ new Date().getFullYear() }}</p>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import CsvImport from './components/CsvImport.vue';
import BudgetTracker from './components/BudgetTracker.vue';

// Configure the base URL for your API
const API_URL = 'http://localhost:8000'; // Change this to deployed API URL in production

export default {
  components: {
    CsvImport,
    BudgetTracker
  },
  data() {
    return {
      newExpense: {
        description: '',
        amount: ''
      },
      expenses: [],
      isLoading: false,
      isSubmitting: false,
      error: null,
      expenseCountChanged: false
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
        
        // Trigger the animation
        this.expenseCountChanged = true;
        setTimeout(() => {
          this.expenseCountChanged = false;
        }, 600);
        
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
    getTotalAmount() {
      const total = this.expenses.reduce((sum, expense) => sum + expense.amount, 0);
      return total.toFixed(2);
    }
  }
}
</script>

<style>
/* General styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: #edf2f7; /* Darker background for better contrast */
  background-image: linear-gradient(to right, rgba(237, 242, 247, 0.7) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(237, 242, 247, 0.7) 1px, transparent 1px);
  background-size: 20px 20px; /* Subtle pattern */
  color: #333;
  line-height: 1.5;
}

.expense-tracker {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.container {
  width: 100%;
  padding: 0 20px;
}

/* Navigation */
.navbar {
  background-color: #2563eb; /* Darker blue */
  color: white;
  padding: 1.25rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  width: 100%; /* Ensure full width */
}

.navbar .container {
  max-width: 100%; /* Full width container */
  display: flex;
  justify-content: center; /* Center title */
}

.app-title {
  font-size: 1.75rem;
  font-weight: 700;
  text-align: center;
}

/* Main content */
.main-container {
  flex: 1;
  padding: 2.5rem 0;
  margin-bottom: 0;
}

.csv-import-wrapper {
  max-width: 80%;
  margin: 0 auto 2rem auto;
}

.budget-tracker-wrapper {
  margin-top: 2rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  max-width: 90%; /* Wider content area */
  margin: 0 auto;
  padding: 0 20px;
}

@media (min-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr 1fr; /* Equal width columns */
    max-width: 80%; /* Control the width of the grid */
  }
}

/* Cards */
.card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 2rem; /* More padding */
  height: 100%; /* Full height */
  min-height: 350px; /* Minimum height */
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 1.5rem; /* Larger title */
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #f0f4f8;
  padding-bottom: 0.75rem;
  text-align: center; /* Center title */
}

/* Form styling */
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #4a5568;
}

.form-input {
  width: 100%;
  padding: 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  background-color: #f9fafc;
}

.form-input::placeholder {
  color: #a0aec0;
  font-style: italic;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
  background-color: white;
}

.amount-input-container {
  position: relative;
}

.currency-symbol {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: #4a5568;
  font-weight: 500;
}

.amount-input {
  padding-left: 1.75rem;
}

.submit-button {
  width: 100%;
  padding: 1rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem; /* Larger font */
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
  margin-top: 1rem; /* Extra space above button */
}

.submit-button:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 6px 8px rgba(37, 99, 235, 0.25);
}

.submit-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.submit-button:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Expenses list styling */
.expenses-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  position: relative; 
  padding-right: 10px; /* Add some padding on right side */
}

/* Expenses list title specifically */
.list-column .card-title {
  margin-right: 90px; /* Space for the badge */
}

.expense-count {
  background-color: #dbeafe;
  color: #1e40af;
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(30, 64, 175, 0.1);
  position: absolute; /* Position it absolutely */
  right: 10px; /* Position it on the right */
  top: 0; /* Align with the top */
  transition: all 0.3s ease; /* Smooth transition for count changes */
}

/* Animation for when expense count changes */
@keyframes badgePulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.expense-count-changed {
  animation: badgePulse 0.5s ease;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0; /* More vertical centering */
  color: #4b5563;
  height: 70%; /* Better centering */
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  margin-bottom: 1rem;
  color: #3b82f6;
  opacity: 0.7;
}

.empty-text {
  font-size: 1.125rem;
  text-align: center;
  max-width: 80%;
  color: #64748b;
}

/* Table styling */
.expense-table-container {
  overflow-x: auto;
}

.expense-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.table-header {
  text-align: left;
  padding: 0.875rem 1rem;
  background-color: #f8fafc;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #4b5563;
}

.description-header {
  text-align: left;
  border-top-left-radius: 6px;
}

.amount-header {
  text-align: right;
}

.category-header {
  text-align: center;
  border-top-right-radius: 6px;
}

.expense-row {
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.15s;
}

.expense-row:hover {
  background-color: #f8fafc;
}

.expense-row:last-child {
  border-bottom: none;
}

.expense-row td {
  padding: 1rem;
}

.description-cell {
  text-align: left;
  font-weight: 400;
}

.amount-cell {
  text-align: right;
  font-weight: 600;
  color: #2d3748;
}

.category-cell {
  text-align: center;
}

.category-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Category colors */
.category-food {
  background-color: #dcfce7;
  color: #166534;
}

.category-shopping {
  background-color: #dbeafe;
  color: #1e40af;
}

.category-furniture {
  background-color: #ffedd5;
  color: #9a3412;
}

.category-transportation {
  background-color: #f3e8ff;
  color: #6b21a8;
}

.category-entertainment {
  background-color: #fce7f3;
  color: #9d174d;
}

.category-utilities {
  background-color: #fef9c3;
  color: #854d0e;
}

.category-housing {
  background-color: #e0e7ff;
  color: #3730a3;
}

.category-healthcare {
  background-color: #fee2e2;
  color: #b91c1c;
}

.category-other {
  background-color: #f3f4f6;
  color: #4b5563;
}

.total-amount {
  text-align: right;
  font-weight: 600;
  padding: 0.75rem 1rem;
  color: #2d3748;
  border-top: 1px solid #e5e7eb;
  margin-top: 0.5rem;
  font-size: 1.125rem;
}

/* Loading state */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  height: 70%;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.75rem;
}

.loading-text {
  color: #6b7280;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Footer */
.footer {
  background-color: #f8fafc;
  padding: 1.25rem 0;
  margin-top: 2rem;
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.02);
  width: 100%;
}

.footer-text {
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Mobile responsiveness enhancements */
@media (max-width: 640px) {
  .navbar {
    padding: 1rem 0;
  }
  
  .app-title {
    font-size: 1.5rem;
  }
  
  .main-container {
    padding: 1.5rem 0;
  }
  
  .content-grid {
    max-width: 95%;
  }
  
  .card {
    padding: 1.5rem;
    min-height: 300px;
  }
  
  .card-title {
    font-size: 1.25rem;
  }
  
  .empty-state {
    padding: 2.5rem 0;
  }
  
  .empty-icon {
    width: 3rem;
    height: 3rem;
  }
  
  .submit-button {
    padding: 0.875rem 1rem;
  }
}
</style>