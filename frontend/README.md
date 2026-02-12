# Vending Machine - Frontend

## Project Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Install Dependencies
```sh
npm install
```

### Compile and Hot-Reload for Development
```sh
npm run dev
```

### Compile and Minify for Production
```sh
npm run build
```

## Docker Usage

To run the full stack (Frontend + Backend + DB) using Docker:

1. Navigate to the docker directory:
   ```sh
   cd ../infrastructure/docker
   ```

2. Start the services:
   ```sh
   docker-compose up --build
   ```

The frontend will be available at `http://localhost:3000`.
