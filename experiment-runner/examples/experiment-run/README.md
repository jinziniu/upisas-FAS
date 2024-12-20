# CrowdNav-FAS2024 Project

## Overview

The **CrowdNav-FAS2024** project is designed to simulate and optimize dynamic traffic routing in a controlled environment using reinforcement learning techniques. This system incorporates a Docker-based CrowdNav simulator and a Deep Q-Network (DQN) adaptation strategy for determining optimal traffic flow configurations. The ultimate goal is to minimize trip overhead while maintaining system efficiency.

## Features

- **Reinforcement Learning Integration**: Implements a DQN-based `ReactiveAdaptationManager` to adapt system parameters dynamically.
- **CrowdNav Simulation**: Utilizes a Dockerized CrowdNav environment for realistic traffic simulations.
- **Dynamic Optimization**: Adjusts parameters like exploration percentage, edge duration factors, and route randomness for optimized performance.
- **Comprehensive Experimentation**: Includes tools for running multiple experiment configurations and collecting performance metrics.

## Key Components

### 1. **RunnerConfig**

Manages the experiment lifecycle, including initialization, execution, and data collection. Key methods include:

- `create_run_table_model`: Defines experiment configurations and factors.
- `start_run`: Trains the DQN model over 1000 epochs and uses the final parameters to interact with the CrowdNav API.
- `populate_run_data`: Collects and formats results for analysis.

### 2. **ReactiveAdaptationManager**

Implements the reinforcement learning logic using:

- Neural networks for Q-value predictions.
- Memory replay for training stability.
- Parameter adjustment based on learned policies.

### 3. **CrowdNav Environment**

Simulates dynamic traffic scenarios and provides an API for interacting with the system.

## Project Workflow

1. **Initialization**
   - The `RunnerConfig` initializes the CrowdNav simulator and `ReactiveAdaptationManager`.
2. **Training**
   - The DQN model is trained over 1000 epochs, starting from an initial state of `[0.0, 0.0, 0.0]`.
3. **Parameter Optimization**
   - The `ReactiveAdaptationManager` selects optimal parameters using Q-value predictions.
4. **Execution**
   - Final parameters are sent to the CrowdNav API to calculate the optimal `trip overhead`.
5. **Result Collection**
   - Performance metrics, including response status, response body, and trip overhead, are stored for analysis.

## Configuration

### Key Parameters

- **Experiment Name**: `crowdnav_api_experiment 0.1`

- **Simulation API Endpoint**: `http://localhost:8080`

- Reinforcement Learning Parameters

  :

  - `explorationPercentage`: Initial value: `0.1`
  - `averageEdgeDurationFactor`: Initial value: `0.5`
  - `routeRandomSigma`: Initial value: `0.2`

### Example Payload for API

```json
{
    "exploration_percentage": 0.15,
    "average_edge_duration_factor": 0.7,
    "route_random_sigma": 0.3
}
```



## Dependencies

- Python 3.8+
- NumPy
- Requests
- TensorFlow/Keras
- Docker

