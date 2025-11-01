import wandb 
import weave
import numpy as np
import random
from typing import Dict, List, Any
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from oai_client import analyze_medical_bill, bills_collection
from openai import OpenAI

# Initialize wandb
wandb.init(
    project="medical-bill-rl",
    name="bill-analysis-agent",
    config={
        "learning_rate": 0.001,
        "episodes": 100,
        "reward_threshold": 0.8,
        "model": "gpt-4"
    }
)

class MedicalBillRLAgent:
    """
    Simple RL agent that learns to improve medical bill analysis
    by getting feedback on its recommendations
    """
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.episode_rewards = []
        self.analysis_history = []
        
    def get_pending_bills(self) -> List[Dict]:
        """Get bills that need analysis"""
        return list(bills_collection.find({"status": "pending"}))
    
    def analyze_bill_with_confidence(self, bill_id: str) -> Dict[str, Any]:
        """Analyze bill and return confidence score"""
        try:
            result = analyze_medical_bill(bill_id)
            
            # Simple confidence scoring based on analysis length and specificity
            analysis_text = result.get("analysis", "")
            confidence = min(1.0, len(analysis_text.split()) / 200)  # Normalize by word count
            
            result["confidence"] = confidence
            return result
        except Exception as e:
            return {"error": str(e), "confidence": 0.0}
    
    def calculate_reward(self, analysis_result: Dict, feedback: Dict = None) -> float:
        """
        Calculate reward based on analysis quality
        In a real system, this would come from user feedback
        """
        if "error" in analysis_result:
            return -1.0
        
        # Simple reward based on confidence and analysis completeness
        confidence = analysis_result.get("confidence", 0)
        analysis = analysis_result.get("analysis", "")
        
        # Check for key elements in analysis
        key_elements = [
            "billing error", "overcharge", "duplicate", "CPT code", 
            "insurance", "dispute", "legal", "recommendation"
        ]
        
        element_score = sum(1 for element in key_elements if element.lower() in analysis.lower())
        element_score = element_score / len(key_elements)  # Normalize
        
        # Combine confidence and completeness
        reward = (confidence * 0.6) + (element_score * 0.4)
        
        # Add feedback bonus if available
        if feedback:
            feedback_score = feedback.get("helpful", 0.5)  # 0-1 scale
            reward = (reward * 0.7) + (feedback_score * 0.3)
        
        return reward
    
    def train_episode(self) -> float:
        """Run one training episode"""
        pending_bills = self.get_pending_bills()
        
        if not pending_bills:
            print("No pending bills found for training")
            return 0.0
        
        # Select random bill for this episode
        bill = random.choice(pending_bills)
        bill_id = bill["id"]
        
        print(f"Training on bill: {bill_id}")
        
        # Analyze the bill
        analysis_result = self.analyze_bill_with_confidence(bill_id)
        
        # Simulate feedback (in real system, this would come from users/experts)
        simulated_feedback = self.simulate_expert_feedback(analysis_result)
        
        # Calculate reward
        reward = self.calculate_reward(analysis_result, simulated_feedback)
        
        # Log to wandb
        wandb.log({
            "episode_reward": reward,
            "confidence": analysis_result.get("confidence", 0),
            "bill_id": bill_id,
            "analysis_length": len(analysis_result.get("analysis", "")),
        })
        
        # Store for learning
        self.episode_rewards.append(reward)
        self.analysis_history.append({
            "bill_id": bill_id,
            "reward": reward,
            "analysis": analysis_result
        })
        
        return reward
    
    def simulate_expert_feedback(self, analysis_result: Dict) -> Dict:
        """
        Simulate expert feedback on the analysis
        In a real system, this would come from medical billing experts
        """
        analysis = analysis_result.get("analysis", "").lower()
        
        # Simple heuristic scoring
        helpful_score = 0.5  # baseline
        
        # Bonus for mentioning specific issues
        if "cpt code" in analysis:
            helpful_score += 0.1
        if "duplicate" in analysis:
            helpful_score += 0.1
        if "overcharge" in analysis:
            helpful_score += 0.1
        if "dispute" in analysis:
            helpful_score += 0.1
        if "legal" in analysis:
            helpful_score += 0.1
        
        # Cap at 1.0
        helpful_score = min(1.0, helpful_score)
        
        return {"helpful": helpful_score}
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        if not self.episode_rewards:
            return {"avg_reward": 0, "total_episodes": 0}
        
        return {
            "avg_reward": np.mean(self.episode_rewards),
            "total_episodes": len(self.episode_rewards),
            "best_reward": max(self.episode_rewards),
            "recent_avg": np.mean(self.episode_rewards[-10:]) if len(self.episode_rewards) >= 10 else np.mean(self.episode_rewards)
        }

def run_rl_training():
    """Main training loop"""
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Create RL agent
    agent = MedicalBillRLAgent(client)
    
    print("Starting RL training for medical bill analysis...")
    
    # Training loop
    for episode in range(wandb.config.episodes):
        print(f"\nEpisode {episode + 1}/{wandb.config.episodes}")
        
        reward = agent.train_episode()
        
        # Log performance metrics
        metrics = agent.get_performance_metrics()
        wandb.log({
            "episode": episode + 1,
            "avg_reward": metrics["avg_reward"],
            "recent_avg_reward": metrics["recent_avg"]
        })
        
        print(f"Episode reward: {reward:.3f}")
        print(f"Average reward: {metrics['avg_reward']:.3f}")
        
        # Early stopping if performance is good
        if metrics["recent_avg"] > wandb.config.reward_threshold:
            print(f"Reached reward threshold! Stopping early at episode {episode + 1}")
            break
    
    # Final metrics
    final_metrics = agent.get_performance_metrics()
    print(f"\nTraining completed!")
    print(f"Final average reward: {final_metrics['avg_reward']:.3f}")
    print(f"Best reward: {final_metrics['best_reward']:.3f}")
    print(f"Total episodes: {final_metrics['total_episodes']}")
    
    wandb.finish()
    return agent

if __name__ == "__main__":
    agent = run_rl_training()