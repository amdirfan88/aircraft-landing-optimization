from pathlib import Path
from urllib.request import urlretrieve

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

url = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/airland7.txt"
destination = data_dir / "airland7.txt"

urlretrieve(url, destination)

print(f"Downloaded: {destination}")
