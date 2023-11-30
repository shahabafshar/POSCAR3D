import json
from pymatgen.core.periodic_table import Element
import random

def rgba_color():
    # Generates a random RGBA color
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    a = 255  # Opaque
    return (r, g, b, a)

# Generate atomic data using pymatgen
atomic_data = {}
for el in Element:
    try:
        # Get a set of properties for each element
        # Fallback values or omissions for missing properties can be handled here
        atomic_data[el.symbol] = {
            "atomic_mass": el.atomic_mass,
            "atomic_radius": el.atomic_radius if el.atomic_radius is not None else "unknown",
            "van_der_waals_radius": el.van_der_waals_radius if el.van_der_waals_radius is not None else "unknown",
            "electronic_structure": el.full_electronic_structure if el.full_electronic_structure is not None else "unknown",
            "color": rgba_color(),  # Random color for each element
            "number_of_electrons": el.Z
        }
    except Exception as e:
        print(f"Could not process element {el.symbol}: {e}")

# Save the atomic data to a JSON file
with open('atomic_data.json', 'w') as f:
    json.dump(atomic_data, f, indent=4)

print("Atomic data JSON file has been created.")
