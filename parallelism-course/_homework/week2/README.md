Через Docker Compose можно поднять базу, API платежей и API страховки:

```bash
docker compose up -d db payment-api protection-api
```

База будет доступна на порту `7432`, API платежей (`payment`) на `9001`, API страховки (`protection`) на `9002`.
