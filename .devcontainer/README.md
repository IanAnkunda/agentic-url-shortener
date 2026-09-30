# GitHub Codespaces

This repository includes a Codespaces/dev-container configuration with Java 21, Maven, Python 3.12, Docker, and VS Code extensions.

After the codespace opens, verify the environment:

```bash
java -version && mvn -version && python3 --version && docker --version && docker compose version
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run the backend:

```bash
cd backend && mvn spring-boot:run
```

In a second terminal, run the orchestrator tests:

```bash
python3 -m unittest orchestrator/test_engine.py
```
