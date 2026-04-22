# NewsHub

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 21.1.4.

## Reprendre le projet

Si tu pars de zéro, fais d'abord tourner la base MySQL et l'API Python, puis démarre le front Angular.

1. Crée la base `NewsHub` avec le script `api/init_db.sql`.
2. Installe les dépendances Python du dossier `api` avec `pip install -r requirements.txt`.
3. Lance l'API avec `uvicorn main:app --reload` depuis le dossier `api`.
4. Installe les dépendances du front avec `npm install` à la racine du projet.
5. Lance le front avec `npm start`.

Si tu avais déjà créé une ancienne base, recrée-la avec le script SQL, parce que la table `users` stocke maintenant un `password_hash`.

Le front utilise l'API Python sur `http://127.0.0.1:8000` pour l'inscription, la connexion et les intérêts.
Les articles de news viennent de l'API NewsData externe, donc ils peuvent s'afficher même si ta base est vide.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
