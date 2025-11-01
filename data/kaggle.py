import kagglehub

# Download latest version
path = kagglehub.dataset_download("huzzefakhan/medical-billing-b2health-care-data-us")

print("Path to dataset files:", path)