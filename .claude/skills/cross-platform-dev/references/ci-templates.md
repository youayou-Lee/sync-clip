# CI/CD Templates for Cross-Platform Development

## GitHub Actions Templates

### Basic Multi-Platform Matrix

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, '3.10', 3.11]
        exclude:
          # Exclude specific combinations if needed
          - os: windows-latest
            python-version: 3.8

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'

    - name: Install system dependencies (Ubuntu)
      if: matrix.os == 'ubuntu-latest'
      run: |
        sudo apt-get update
        sudo apt-get install -y libcairo2-dev libgirepository1.0-dev

    - name: Install system dependencies (macOS)
      if: matrix.os == 'macos-latest'
      run: |
        brew install cairo gobject-introspection

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Lint
      run: |
        flake8 src tests
        mypy src

    - name: Test
      run: |
        pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.10'
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Build and Release Workflow

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build pyinstaller

    - name: Build wheel
      run: python -m build

    - name: Build executable (Linux)
      if: matrix.os == 'ubuntu-latest'
      run: |
        pyinstaller --onefile --name myapp-linux src/main.py

    - name: Build executable (Windows)
      if: matrix.os == 'windows-latest'
      run: |
        pyinstaller --onefile --name myapp.exe src/main.py

    - name: Build executable (macOS)
      if: matrix.os == 'macos-latest'
      run: |
        pyinstaller --onefile --name myapp-macos src/main.py
        create-dmg dist/myapp-macos dist/myapp-macos.dmg

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist-${{ matrix.os }}
        path: dist/

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Download all artifacts
      uses: actions/download-artifact@v3

    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          dist-ubuntu-latest/*
          dist-windows-latest/*
          dist-macos-latest/*
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Docker Build Matrix

```yaml
name: Docker Build

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        platform: [linux/amd64, linux/arm64]

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to Docker Hub
      if: github.ref == 'refs/heads/main'
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        platforms: ${{ matrix.platform }}
        push: ${{ github.ref == 'refs/heads/main' }}
        tags: |
          myorg/myapp:latest
          myorg/myapp:${{ github.sha }}
```

## GitLab CI Templates

### Multi-Platform GitLab CI

```yaml
stages:
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .venv/

.test-template: &test-template
  stage: test
  before_script:
    - python -m venv .venv
    - source .venv/bin/activate
    - pip install --upgrade pip
    - pip install -r requirements-dev.txt
  script:
    - flake8 src tests
    - mypy src
    - pytest tests/ -v --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

python-3.8:
  image: python:3.8
  <<: *test-template

python-3.9:
  image: python:3.9
  <<: *test-template

python-3.10:
  image: python:3.10
  <<: *test-template

python-3.11:
  image: python:3.11
  <<: *test-template

windows:
  stage: test
  tags:
    - windows
  script:
    - python -m pip install --upgrade pip
    - pip install -r requirements-dev.txt
    - pytest tests/ -v
  only:
    - main
    - develop

macos:
  stage: test
  tags:
    - macos
  script:
    - python3 -m pip install --upgrade pip
    - pip3 install -r requirements-dev.txt
    - pytest3 tests/ -v
  only:
    - main
    - develop

build:
  stage: build
  image: python:3.10
  script:
    - python -m pip install --upgrade pip build
    - python -m build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour
  only:
    - main
    - tags

deploy:
  stage: deploy
  image: python:3.10
  script:
    - pip install --upgrade pip twine
    - twine upload dist/*
  only:
    - tags
```

## Jenkins Pipeline Templates

### Declarative Pipeline for Cross-Platform

```groovy
pipeline {
    agent none

    environment {
        DOCKER_REGISTRY = 'myregistry.com'
        IMAGE_NAME = 'myapp'
    }

    stages {
        stage('Test') {
            parallel {
                stage('Linux Python 3.8') {
                    agent {
                        docker {
                            image 'python:3.8'
                        }
                    }
                    steps {
                        sh 'pip install -r requirements-dev.txt'
                        sh 'pytest tests/'
                    }
                }
                stage('Linux Python 3.9') {
                    agent {
                        docker {
                            image 'python:3.9'
                        }
                    }
                    steps {
                        sh 'pip install -r requirements-dev.txt'
                        sh 'pytest tests/'
                    }
                }
                stage('Windows') {
                    agent {
                        label 'windows'
                    }
                    steps {
                        bat 'python -m pip install -r requirements-dev.txt'
                        bat 'pytest tests/'
                    }
                }
                stage('macOS') {
                    agent {
                        label 'macos'
                    }
                    steps {
                        sh 'python3 -m pip install -r requirements-dev.txt'
                        sh 'pytest3 tests/'
                    }
                }
            }
        }

        stage('Build') {
            when {
                anyOf {
                    branch 'main'
                    buildingTag()
                }
            }
            parallel {
                stage('Linux Build') {
                    agent {
                        docker {
                            image 'python:3.10'
                        }
                    }
                    steps {
                        sh 'python -m pip install build'
                        sh 'python -m build'
                        archiveArtifacts artifacts: 'dist/*', fingerprint: true
                    }
                }
                stage('Windows Build') {
                    agent {
                        label 'windows'
                    }
                    steps {
                        bat 'python -m pip install pyinstaller'
                        bat 'pyinstaller --onefile src/main.py'
                        archiveArtifacts artifacts: 'dist/*.exe', fingerprint: true
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                buildingTag()
            }
            agent {
                label 'linux'
            }
            steps {
                script {
                    def tagName = env.TAG_NAME
                    sh "docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${tagName} ."
                    withCredentials([usernamePassword(credentialsId: 'docker-registry', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh "docker login ${DOCKER_REGISTRY} -u ${DOCKER_USER} -p ${DOCKER_PASS}"
                        sh "docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${tagName}"
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            mail to: 'team@example.com',
                subject: "Pipeline succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build succeeded. Check ${env.BUILD_URL}"
        }
        failure {
            mail to: 'team@example.com',
                subject: "Pipeline failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build failed. Check ${env.BUILD_URL}"
        }
    }
}
```

## Azure DevOps Templates

### Azure Pipelines YAML

```yaml
trigger:
  branches:
    include:
    - main
    - develop
  tags:
    include:
    - v*

pr:
  branches:
    include:
    - main

variables:
  pythonVersion: '3.10'

stages:
- stage: Test
  displayName: Test Stage
  jobs:
  - job: TestLinux
    displayName: Test on Linux
    strategy:
      matrix:
        Python38:
          pythonVersion: '3.8'
        Python39:
          pythonVersion: '3.9'
        Python310:
          pythonVersion: '3.10'
        Python311:
          pythonVersion: '3.11'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'

    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
      displayName: 'Install dependencies'

    - script: |
        flake8 src tests
        mypy src
      displayName: 'Lint'

    - script: |
        pytest tests/ -v --cov=src --cov-report=xml
      displayName: 'Test'

    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs:
        testResultsFiles: 'junit.xml'
        testRunTitle: 'Linux Python $(pythonVersion)'

    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: Cobertura
        summaryFileLocation: 'coverage.xml'

  - job: TestWindows
    displayName: Test on Windows
    pool:
      vmImage: 'windows-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'

    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
      displayName: 'Install dependencies'

    - script: |
        pytest tests/ -v
      displayName: 'Test'

  - job: TestMacOS
    displayName: Test on macOS
    pool:
      vmImage: 'macOS-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'

    - script: |
        python3 -m pip install --upgrade pip
        pip3 install -r requirements-dev.txt
      displayName: 'Install dependencies'

    - script: |
        pytest3 tests/ -v
      displayName: 'Test'

- stage: Build
  displayName: Build Stage
  dependsOn: Test
  condition: and(succeeded(), or(eq(variables['Build.SourceBranch'], 'refs/heads/main'), startsWith(variables['Build.SourceBranch'], 'refs/tags/')))
  jobs:
  - job: Build
    strategy:
      matrix:
        Linux:
          vmImage: 'ubuntu-latest'
        Windows:
          vmImage: 'windows-latest'
        macOS:
          vmImage: 'macOS-latest'
    pool:
      vmImage: $(vmImage)
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'

    - script: |
        python -m pip install --upgrade pip build pyinstaller
      displayName: 'Install build tools'

    - ${{ if eq(variables['vmImage'], 'ubuntu-latest') }}:
      - script: |
          python -m build
        displayName: 'Build wheel'

    - ${{ if ne(variables['vmImage'], 'ubuntu-latest') }}:
      - script: |
          pyinstaller --onefile --name myapp-$(Agent.OS) src/main.py
        displayName: 'Build executable'

    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: 'dist'
        artifactName: 'dist-$(Agent.OS)'
```

## Best Practices

### 1. Matrix Strategies
- Test on all target platforms
- Test multiple Python/Node/Go versions
- Use `fail-fast: false` to get all results

### 2. Caching
- Cache dependencies between runs
- Cache Docker layers
- Use proper cache keys for different platforms

### 3. Security
- Use secrets for sensitive data
- Scan dependencies for vulnerabilities
- Sign binaries before release

### 4. Notifications
- Notify team on failures
- Integrate with Slack/Teams
- Use appropriate escalation paths

### 5. Performance
- Parallelize independent jobs
- Use self-hosted runners for faster builds
- Optimize Docker images

### 6. Artifact Management
- Clean up old artifacts
- Use appropriate retention policies
- Tag releases properly