from fuzzywuzzy import process

def get_closest_name(spoken_name, known_names):
    # Try to find the closest match with a threshold
    matches = process.extract(spoken_name, known_names, limit=3)
    

    suggestions = [name for name, score in matches]
    print(f"There is no user named '{spoken_name}', did you mean: {', '.join(suggestions)}?")
    return None

# Example usage
known_names = ["Johanathan", "Joni", "Joker", "John"]
spoken_name = "John"  # Simulating voice input
result = get_closest_name(spoken_name, known_names)

if result:
    print(f"User identified: {result}")
else:
    print("User not identified.")
