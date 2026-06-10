# Toolforge Monitoring Probes

Prometheus metric exporter which runs checks specific to toolforge components.

## Testing locally

```
$ fastapi dev monitoring_toolforge/api.py 
```

## Build locally

```
$ pack build --builder heroku/builder:24 monitoring-toolforge
```

## Production configuration

- NFS must be mounted (k8s certs required for API authentication)
