echo "version:" $1
gcloud app deploy --version=$1 ./app.yaml ./module-worker.yaml
