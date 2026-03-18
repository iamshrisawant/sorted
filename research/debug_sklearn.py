from sklearn.datasets import get_data_home
print(f"Scikit-learn data home: {get_data_home()}")

try:
    from sklearn.datasets import fetch_20newsgroups
    # Try fetching just headers to see if it finds it
    d = fetch_20newsgroups(subset='train', categories=['sci.med'], download_if_missing=False)
    print("Found dataset!")
except Exception as e:
    print(f"Error: {e}")
