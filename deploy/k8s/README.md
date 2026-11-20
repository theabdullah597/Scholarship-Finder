# Kubernetes deployment

The manifests in `app.yaml` provide a production starting point for the API,
worker, web, PostgreSQL, and Redis services. Replace the placeholder secret
values and image names before applying them:

```powershell
kubectl apply -f deploy\k8s\app.yaml
```

For production, use managed PostgreSQL/Redis or replace the included stateful
workloads with the organization's approved operators and storage classes.
