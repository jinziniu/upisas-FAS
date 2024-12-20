from pathlib import Path
from typing import Dict, Any, Optional
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
import requests
from UPISAS.exemplars.crodnav import CrowdnavFAS2024
from UPISAS.strategies.dqnStrategy import ReactiveAdaptationManager
import numpy as np


class RunnerConfig:
    ROOT_DIR = Path(__file__).parent
    name: str = "crowdnav_api_experiment 0.1"
    results_output_path: Path = ROOT_DIR / "experiments"
    time_log_path: Path = Path(r"E:\Python\projects\UPISAS\time_log.txt")
    operation_type: OperationType = OperationType.AUTO
    BASE_URL = "http://localhost:8080"

    def __init__(self):
        self.results_output_path.mkdir(parents=True, exist_ok=True)
        print("Custom config initialized with results_output_path:", self.results_output_path)

        self.crowdnav = CrowdnavFAS2024(auto_start=True)
        self.reactive_manager = ReactiveAdaptationManager(
            state_size=3,
            action_size=1000,
            initial_params={
                "explorationPercentage": 0.1,
                "averageEdgeDurationFactor": 0.5,
                "routeRandomSigma": 0.2,
            },
        )

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN, self.before_run),
            (RunnerEvents.START_RUN, self.start_run),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT, self.interact),
            (RunnerEvents.STOP_MEASUREMENT, self.stop_measurement),
            (RunnerEvents.STOP_RUN, self.stop_run),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT, self.after_experiment)
        ])

        self.run_table_model = None
        output.console_log("Custom config loaded for CrowdNav")

    def create_run_table_model(self) -> RunTableModel:
        factor1 = FactorModel("api_endpoint", ["/monitor", "/adaptation_options", "/execute"])
        factor2 = FactorModel("method", ["GET", "PUT"])
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_variations=[
                {factor1: ["/monitor"], factor2: ["PUT"]},
                {factor1: ["/adaptation_options"], factor2: ["PUT"]},
                {factor1: ["/execute"], factor2: ["GET"]}
            ],
            repetitions=3,
            data_columns=["response_status", "response_body", "system_performance"]
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        output.console_log("Config.before_experiment() called!")

    def start_run(self, context: RunnerContext) -> None:
        initial_state = np.array([[0.0, 0.0, 0.0]])  # Initial state
        epochs = 1000

        for epoch in range(epochs):
            # Analyze current state
            analysis_data = self.reactive_manager.analyze(initial_state)
            # Plan based on analysis
            plan_data = self.reactive_manager.plan()

            exploration_percentage = plan_data["explorationPercentage"]
            average_edge_duration_factor = plan_data["averageEdgeDurationFactor"]
            route_random_sigma = plan_data["routeRandomSigma"]

            # Simulate an environment step (replace this with actual environment logic)
            next_state = initial_state + np.random.normal(0, 0.01, initial_state.shape)
            reward = -np.sum(np.abs(next_state - 0.5))  # Example reward function
            done = epoch == (epochs - 1)

            # Step the manager
            self.reactive_manager.step(initial_state, reward, next_state, done)
            initial_state = next_state

        # After training, use the final parameters for execution
        final_plan = self.reactive_manager.plan()

        payload = {
            "exploration_percentage": final_plan["explorationPercentage"],
            "average_edge_duration_factor": final_plan["averageEdgeDurationFactor"],
            "route_random_sigma": final_plan["routeRandomSigma"]
        }

        try:
            response = requests.put(f"{self.BASE_URL}/execute", json=payload)
            response.raise_for_status()
            response_data = response.json()

            trip_overhead = response_data.get("trip_overhead", "No Data")
            output.console_log(f"Optimal Trip Overhead: {trip_overhead}")

            context.run_data = {
                "response_status": response.status_code,
                "response_body": response_data,
                "trip_overhead": trip_overhead,
            }
        except Exception as e:
            output.console_log(f"Error during API call: {e}")
            context.run_data = {
                "response_status": "ERROR",
                "response_body": str(e),
                "trip_overhead": "N/A",
            }

    def start_measurement(self, context: RunnerContext) -> None:
        output.console_log("Config.start_measurement() called!")

    def interact(self, context: RunnerContext) -> None:
        output.console_log("Config.interact() called!")

    def stop_measurement(self, context: RunnerContext) -> None:
        output.console_log("Config.stop_measurement() called!")

    def stop_run(self, context: RunnerContext) -> None:
        output.console_log("Config.stop_run() called!")

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        run_data = context.run_data if context.run_data else {}
        return {
            "api_endpoint": context.run_variation.get("api_endpoint", "N/A"),
            "method": context.run_variation.get("method", "N/A"),
            "response_status": run_data.get("response_status", "N/A"),
            "response_body": run_data.get("response_body", "N/A"),
            "trip_overhead": run_data.get("trip_overhead", "N/A"),
        }

    def after_experiment(self) -> None:
        output.console_log("Config.after_experiment() called!")
        self.crowdnav.stop_container()

if __name__ == "__main__":
    config = RunnerConfig()
    config.run_table_model = config.create_run_table_model()
