import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const featureName = process.argv[2];

if (!featureName) {
    console.error("Usage: npm run generate:feature -- <feature-name>");
    process.exit(1);
}

if (!/^[a-z][a-z0-9-]*$/.test(featureName)) {
    console.error(
        "Feature name must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens.",
    );
    process.exit(1);
}

const featurePath = path.resolve(
    import.meta.dirname,
    "../src/features",
    featureName,
);

if (existsSync(featurePath)) {
    console.error(`Feature already exists: ${featureName}`);
    process.exit(1);
}

const directories = [
    "api",
    "components",
    "hooks",
    "types",
    "__tests__",
];

mkdirSync(featurePath, { recursive: true });

for (const directory of directories) {
    mkdirSync(path.join(featurePath, directory), { recursive: true });
}

writeFileSync(
    path.join(featurePath, "index.ts"),
    `// Public API for the ${featureName} feature.\n`,
);

console.log(`Feature created successfully: ${featureName}`);
console.log(`Location: ${featurePath}`);
