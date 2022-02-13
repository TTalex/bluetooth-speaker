# run with: python3.8 main.py
import asyncio
from kasa import SmartPlug

async def main():
    p = SmartPlug("192.168.1.94")

    await p.update()
    print(p.alias)

    await p.turn_on()


if __name__ == "__main__":
    asyncio.run(main())

