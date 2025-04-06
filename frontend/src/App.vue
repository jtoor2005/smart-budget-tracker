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
              <svg class