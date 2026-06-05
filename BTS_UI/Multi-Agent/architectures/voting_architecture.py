"""
Voting Architecture

This architecture runs multiple expert agents
and aggregates their results using a simple voting strategy.
"""

import json


class VotingArchitecture:

    def __init__(self, agents):
        """
        Initialize Voting Architecture.

        Args:
            agents (list): List of agent instances
        """

        self.agents = agents

    def run(self, input_data):

        print("===== Running Voting Architecture =====")

        results = []

        for agent in self.agents:

            print(f"\n[Architecture] Running {agent.name}")

            agent_result = agent.run(input_data)

            if isinstance(agent_result, dict):
                agent_result_json = agent_result
            else:
                try:
                    agent_result_json = json.loads(agent_result)
                except Exception as e:
                    print(f"[Architecture] JSON parse failed for {agent.name}: {e}")
                    continue

            results.append({
                "agent": agent.name,
                "result": agent_result_json
            })

        # 2 投票与字段融合
        final_result = self.vote(results)

        print("\n===== Voting Completed =====")

        return final_result

    FIELD_STRATEGY = {
        "tumor_location": "confidence",
        "tumor_analysis": "confidence",
        "severity_assessment": "vote",
        "possible_diagnosis": "vote",
        "recommendation": "confidence",
        "need_doctor_review": "vote_bool",
        "confidence": "max",
        "confidence_reason": "best",
        "remarks": "best"
    }

    def vote(self, results):

        if not results:
            return {"error": "No valid agent results"}

        def normalize_confidence(c):
            try:
                c = float(c)
                return max(0.0, min(1.0, c))
            except:
                return 0.0

        def map_confidence_level(score):
            if score < 0.2:
                return "非常不可靠"
            elif score < 0.4:
                return "不太可靠"
            elif score < 0.6:
                return "比较可靠"
            elif score < 0.8:
                return "可靠"
            else:
                return "非常可靠"

        agent_results = [item["result"] for item in results]

        best_result = max(
            agent_results,
            key=lambda x: normalize_confidence(x.get("confidence", 0))
        )

        final = {}

        for key in best_result.keys():

            if key == "confidence":
                confs = [
                    normalize_confidence(r.get("confidence", 0))
                    for r in agent_results
                ]

                avg_conf = sum(confs) / len(confs)

                final["confidence"] = map_confidence_level(avg_conf)

                continue

            strategy = self.FIELD_STRATEGY.get(key, "confidence")
            values = [r.get(key) for r in agent_results]

            if strategy == "vote":
                counter = {}
                for v in values:
                    counter[v] = counter.get(v, 0) + 1
                final[key] = max(counter, key=counter.get)

            elif strategy == "vote_bool":
                true_count = sum(1 for v in values if v)
                final[key] = true_count >= (len(values) / 2)

            elif strategy == "confidence":
                best_value = None
                best_score = -1

                for r in agent_results:
                    score = normalize_confidence(r.get("confidence", 0))
                    if score > best_score:
                        best_score = score
                        best_value = r.get(key)

                final[key] = best_value

            elif strategy == "max":
                final[key] = best_result.get(key)

            elif strategy == "best":
                final[key] = best_result.get(key)

            else:
                final[key] = best_result.get(key)

        return final