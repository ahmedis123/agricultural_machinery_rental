
📄 simple-interest.sh

#!/bin/bash

# Simple Interest Calculator

echo "=== Simple Interest Calculator ==="

# Read inputs from the user
read -p "Enter the principal amount (P): " principal
read -p "Enter the annual interest rate (R) in %: " rate
read -p "Enter the time (T) in years: " time

# Calculate simple interest
si=$(echo "scale=2; ($principal * $rate * $time) / 100" | bc)

# Display the result
echo "----------------------------------"
echo "Simple Interest = $si"
echo "Total Amount = $(echo "scale=2; $principal + $si" | bc)"
echo "----------------------------------"


---

✅ How to Use It

1. Save the file as simple-interest.sh.


2. Make it executable:

chmod +x simple-interest.sh


3. Run it:

./simple-interest.sh

