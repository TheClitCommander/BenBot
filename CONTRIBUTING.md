# Contributing to BensBot

Thank you for considering contributing to BensBot! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

### Prerequisites
- Python 3.10+
- Node.js 16+
- npm or yarn
- Docker and Docker Compose (optional)

### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bensbot.git
   cd bensbot
   ```

2. Start the development environment:
   ```bash
   # Option 1: Using the startup script
   ./run_bensbot.sh
   
   # Option 2: Using Docker
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

## Code Style and Standards

### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints
- Write docstrings for all functions and classes
- Organize imports alphabetically: standard library, third-party, local
- Use Pydantic models for data validation

### Frontend (TypeScript/React)
- Follow the project's ESLint configuration
- Use functional components with hooks
- Use TypeScript types for all props and state
- Use named exports rather than default exports
- Follow the existing component structure
- Use React Query for data fetching

## Branch Naming Convention

- `feature/short-description` - For new features
- `bugfix/issue-short-description` - For bug fixes
- `refactor/component-name` - For code refactoring
- `docs/short-description` - For documentation changes
- `test/component-name` - For adding missing tests

## Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:

```
<type>(optional scope): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Examples:
- `feat(api): add new strategy endpoints`
- `fix(dashboard): resolve API connection issue`
- `docs: update README with Docker instructions`

## Pull Request Process

1. Create a new branch from `main` following the naming convention
2. Make your changes and commit them with appropriate commit messages
3. Push your branch and create a pull request against `main`
4. Ensure all CI checks pass
5. Request a review from at least one team member
6. Address all review comments
7. Once approved, maintainers will merge your PR

## Testing

### Backend
- Write unit tests using Pytest
- Aim for 80% or higher code coverage
- Run tests with `pytest backend/tests`

### Frontend
- Write component tests using Jest and React Testing Library
- Test hooks with custom hook testing utilities
- Run tests with `cd frontend && npm test`

## Code Review Guidelines

When reviewing code, consider:
1. Does the code meet the project's style guidelines?
2. Is the code well-tested?
3. Is the code efficient and optimized?
4. Is the code secure and free from vulnerabilities?
5. Is the code well-documented?
6. Does the code handle edge cases appropriately?

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [React Query Documentation](https://react-query.tanstack.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pytest Documentation](https://docs.pytest.org/) 