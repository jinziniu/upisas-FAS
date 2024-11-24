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


class RunnerConfig:
    ROOT_DIR = Path(__file__).parent

    # Experiment configuration
    name: str = "crowdnav_api_experiment 0.1"
    results_output_path: Path = ROOT_DIR / "experiments"
    operation_type: OperationType = OperationType.AUTO
    time_between_runs_in_ms: int = 1000
    BASE_URL = "http://localhost:8080"

    def __init__(self):
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
        """Define the experiment factors and run table model."""
        factor1 = FactorModel("api_endpoint", ["/monitor", "/adaptation_options", "/execute"])
        factor2 = FactorModel("method", ["GET", "PUT"])
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_variations=[
                {factor1: ["/monitor"], factor2: ["PUT"]},
                {factor1: ["/adaptation_options"], factor2: ["PUT"]},
                {factor1: ["/execute"], factor2: ["GET"]}  # Exclude unsupported GET for /execute
            ],
            repetitions=3,
            data_columns=["response_status", "response_body", "system_performance"]
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        """Called before the experiment starts."""
        output.console_log("Config.before_experiment() called!")
        print("Debug - Run table model:", self.run_table_model)

    def before_run(self) -> None:
        """Called before each run starts."""
        output.console_log("Config.before_run() called!")

    def start_run(self, context: RunnerContext) -> None:
        """Perform the main logic for each run."""
        run_variation = getattr(context, "run_variation", {})
        print("Debug - Context attributes:", context.__dict__)
        print("Debug - Run variation:", run_variation)

        # Retrieve factors
        endpoint = run_variation.get("api_endpoint", "/monitor")
        method = run_variation.get("method", "GET")
        url = f"{self.BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{self.BASE_URL}/{endpoint}"

        try:
            if method == "GET":
                if endpoint == "/monitor":
                    # Example: Append a timestamp to simulate real-time monitoring
                    response = requests.get(f"{url}?timestamp=now")
                elif endpoint == "/adaptation_options":
                    # Fetch and parse adaptation options with improved error handling
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                        options = response.json()

                        # Validate the returned options (if needed)
                        if not isinstance(options, dict):
                            raise ValueError(f"Unexpected response format for /adaptation_options: {options}")

                        # Log the adaptation options in a structured way
                        output.console_log("Adaptation Options Retrieved Successfully:")
                        for key, value in options.items():
                            output.console_log(f"  {key}: {value}")

                        print("Adaptation Options Available:", options)
                    except requests.RequestException as re:
                        output.console_log(f"Request failed for /adaptation_options: {re}")
                        context.run_data = {
                            "response_status": response.status_code if response else "ERROR",
                            "response_body": str(re),
                            "system_performance": "N/A",
                        }
                    except Exception as e:
                        output.console_log(f"Unexpected error while handling /adaptation_options: {e}")
                        context.run_data = {
                            "response_status": "ERROR",
                            "response_body": str(e),
                            "system_performance": "N/A",
                        }
                    else:
                        context.run_data = {
                            "response_status": response.status_code,
                            "response_body": options,
                            "system_performance": options.get("performance", "No Data"),
                        }
            elif method == "PUT":
                if endpoint == "/execute":
                    # Construct a full payload for the /execute endpoint
                    payload = {
                        "route_random_sigma": 1.5,
                        "exploration_percentage": 0.1,
                        "max_speed_and_length_factor": 2,
                        "average_edge_duration_factor": 3,
                        "freshness_update_factor": 0.8,
                        "freshness_cut_off_value": 15,
                        "re_route_every_ticks": 5,
                        "total_car_counter": 100,
                        "edge_average_influence": 1.2
                    }
                    response = requests.put(url, json=payload)
                    print("Execute API Response:", response.json())
                else:
                    payload = {"example_data": "test_payload"}  # Generic payload for other endpoints
                    response = requests.put(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            # Safely parse the performance datapip install -r requirements.txt
            response_json = response.json() if response.content else {}
            performance = response_json.get("performance", "No Data")
            context.run_data = {
                "response_status": response.status_code,
                "response_body": response_json,
                "system_performance": performance,
            }
        except Exception as e:
            output.console_log(f"Error during API call to {endpoint}: {e}")
            context.run_data = {
                "response_status": "ERROR",
                "response_body": str(e),
                "system_performance": "N/A",
            }

    def start_measurement(self, context: RunnerContext) -> None:
        """Called when measurements start."""
        output.console_log("Config.start_measurement() called!")

    def interact(self, context: RunnerContext) -> None:
        """Interact with the system during the run."""
        output.console_log("Config.interact() called!")

    def stop_measurement(self, context: RunnerContext) -> None:
        """Stop measurement for the run."""
        output.console_log("Config.stop_measurement() called!")

    def stop_run(self, context: RunnerContext) -> None:
        """Stop the current run."""
        output.console_log("Config.stop_run() called!")

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Populate the run data for recording."""
        run_data = context.run_data if context.run_data else {}
        return {
            "api_endpoint": context.run_variation.get("api_endpoint", "N/A"),
            "method": context.run_variation.get("method", "N/A"),
            "response_status": run_data.get("response_status", "N/A"),
            "response_body": run_data.get("response_body", "N/A"),
            "system_performance": run_data.get("system_performance", "N/A"),
        }

    def after_experiment(self) -> None:
        """Called after the experiment ends."""
        output.console_log("Config.after_experiment() called!")


# Entry point for the configuration
if __name__ == "__main__":
    config = RunnerConfig()
    config.run_table_model = config.create_run_table_model()