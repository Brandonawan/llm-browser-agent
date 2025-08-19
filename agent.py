import asyncio
import logging
from browser_use.llm import ChatGoogle
from browser_use import Agent
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenericUIAgent(Agent):
    """
    Generic UI Agent for cross-platform web tasks.
    Extends browser_use.Agent with logging and basic recovery.
    Works across providers by relying on LLM for dynamic UI discovery.
    """
    def __init__(self, task: str, llm, max_retries: int = 3):
        super().__init__(task=task, llm=llm)
        self.max_retries = max_retries
       
        self.provider_hints = {
            'saucedemo': {'success_url': 'inventory.html'},
            'practicetestautomation': {'success_url': 'logged-in-successfully'}
        }  # Use for verification, not core logic

    async def run(self):
        logger.info(f"Starting task: {self.task}")
        try:

            await super().run()
            logger.info("Task completed successfully")
        except Exception as e:
            logger.error(f"Error during task: {str(e)}")
            for attempt in range(1, self.max_retries + 1):
                logger.info(f"Retry attempt {attempt}/{self.max_retries}")
                try:
                    # Stretch: Re-reason with LLM (e.g., prompt for alternative fields)
                    self.task += " (Retry: Analyze page again for fields)"
                    await super().run()
                    logger.info("Recovery successful")
                    break
                except:
                    if attempt == self.max_retries:
                        logger.error("Max retries exceeded. Task failed.")
                        raise

    async def analyze_screenshot(self, page):
        screenshot = await page.screenshot()
        description = self.llm.complete(f"Describe login form in this screenshot: [attach {screenshot}]")
        logger.info(f"Screenshot analysis: {description}")
        return description

async def main():
    llm = ChatGoogle(model="gemini-2.0-flash-exp")
    
    print("Welcome to the Web Action Agent! Type your instruction or 'quit' to exit.")
    print("Example: Login to https://www.saucedemo.com/ with username standard_user and password secret_sauce")
    
    while True:
        instruction = input("\nWhat would you like me to do? ").strip().lower()
        
        if instruction in ["quit", "exit"]:
            logger.info("User requested to exit. Shutting down.")
            print("Goodbye!")
            break
        
        # Validate instruction
        if not instruction:
            logger.warning("No instruction provided.")
            print("Please provide a valid instruction.")
            continue

        enhanced_task = (
            f"{instruction}. "
            "Use reasoning to inspect the DOM, find login form fields dynamically (look for inputs with types text/password, labels like 'username'/'password', placeholders). "
            "Do not hardcode IDs or names. Fill credentials and submit. Verify success by checking for redirect or success message."
        )
        
        # Create and run agent
        agent = GenericUIAgent(task=enhanced_task, llm=llm)
        try:
            await agent.run()
            print("Task completed! Ready for the next instruction.")
            print("------------------------------------------------")
        except Exception as e:
            print(f"Task failed: {str(e)}. Please try again or type a new instruction.")

if __name__ == "__main__":
    asyncio.run(main())
