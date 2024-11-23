def basic_computation(a, b):
    sum_result = a + b
    diff_result = a - b
    prod_result = a * b
    if b != 0:
        div_result = a / b
    else:
        div_result = None

    return {
        'sum': sum_result,
        'difference': diff_result,
        'product': prod_result,
        'division': div_result
    }

if __name__ == '__main__':
    # Example usage
    a = 10
    b = 5
    results = basic_computation(a, b)
    print(f"Sum: {results['sum']}")
    print(f"Difference: {results['difference']}")
    print(f"Product: {results['product']}")
    print(f"Division: {results['division']}")