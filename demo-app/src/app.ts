// BROKEN SOURCE FILE FOR HACKATHON DEMONSTRATION
import { calculateTotal, multiplyNumbers } from "./math";

interface UserCart {
    items: string[];
    price: number;
}

function processOrder(user: string, price: number) {
    console.log(`Processing order for ${user}...`);
    
    // ERROR 1: calculateTotal missing import or signature error
    const total = calculateTotal(price, 0.1);
    
    // ERROR 2: Type mismatch - passing string instead of number
    const result = multiplyNumbers(100, 2);
    
    return { total, result };
}

processOrder("Alex", 250);
