# DevIntel AI Frontend

## Project Overview

**DevIntel AI** is a powerful tool that helps developers understand their codebase instantly. Connect your GitHub repository and get contextual AI insights, refactoring suggestions, and intelligent code explanations.

## Technologies Used

This project is built with modern web technologies:

- **Vite** - Fast build tool and dev server
- **TypeScript** - Type-safe JavaScript
- **React** - UI framework
- **shadcn-ui** - Beautiful component library
- **Tailwind CSS** - Utility-first CSS framework

## Getting Started

### Prerequisites

- Node.js (v18 or higher) - [Install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- npm or yarn package manager

### Installation

Clone the repository and install dependencies:

```sh
# Clone the repository
git clone <YOUR_GIT_URL>

# Navigate to the project directory
cd devintel-frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will be available at `http://localhost:8080`

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run build:dev` - Build in development mode
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm test` - Run tests
- `npm run test:watch` - Run tests in watch mode

## Project Structure

```
devintel-frontend/
├── src/
│   ├── components/     # React components
│   ├── pages/          # Page components
│   ├── lib/            # Utilities and helpers
│   └── main.tsx        # Application entry point
├── public/             # Static assets
└── index.html          # HTML template
```

## Development

### Code Style

This project uses ESLint for code quality. Run `npm run lint` to check your code.

### Testing

Tests are written using Vitest and React Testing Library:

```sh
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch
```

## Deployment

Build the project for production:

```sh
npm run build
```

The optimized files will be in the `dist/` directory, ready to be deployed to any static hosting service.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is private and proprietary.
