def factorial(n: int) -> int:

    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    try:
        num = int(input("Enter a non-negative integer to calculate its factorial: "))
        if num < 0:
            raise ValueError("Factorial is defined only for non-negative integers.")
        
        result = factorial(num)
        print(f"The factorial of {num} is: {result}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()