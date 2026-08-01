import asyncio

from services.graph_service import run_graph


async def main():

    result = await run_graph(
        question="Who earns the highest salary?",
        session_id="demo",
        model="llama-3.3-70b-versatile",
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())