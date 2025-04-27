# Makeathon 2025: Reply Challenge Submission - Aeron

This project was done during Tum.ai Makeathon's 2025. The challenge was building a autonomous drone mapping generation system, with natural language input. In short, give a command and a set of images, return 3D coordinates for drone to fly to.

https://github.com/user-attachments/assets/30bfbee1-e394-4eeb-8693-658ccf7d4a9c

Author:

- **Binh The Bro**: Handles everything related to drone 3D mapping, sfm and point triangulation (colmap and just linear algebra). Handles the web app (nextjs), server (fastapi) and kmz file generation for dji drones.
- **Akshay The Bro**: Handles mlops pipeline, object detection (Yolov11) and object matching (Hungarian Algo and cost matrix).
- **Isha The Sis**: Handles natural language pipeline, data annotation and kmz file generation.
- **Vercel's v0**: Built a website that has 1000 dependencies error that bro Binh can only fix partially but solid contribution.

# Project Dependencies

To run this project, you must have:

- uv: for python env and deps management. You can check the installation here: https://docs.astral.sh/uv/getting-started/installation/
- npm and node: for js server side execution and package management (aka the frontend). https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

# Project Structure

In this repository, you'll find:

- /back_end: to be run with uv
- /front_end: to be run with npm
- /notebooks: the research behind this project, helpful for those who want to understand 3D triangulation.
- /results: end result for the challenge

# Back End

The back end is a fast api server with one primary websocket endpoint. Through this endpoint, user can upload files and send prompts without interuption.

In this directory, you can find main.py as the main execution point, test.py for testing the 3d pipeline test, /modules for every part of the pipeline.

To run back end, you just need to:

```
uv run back_end/main.py
```

# Front End

The front end is a simple reactjs web app made by Vercel v0, upgraded with api controls from a human. Therefore. instead of using npm install, you need to use:

```
npm install --force
npm run dev
```

# Notebooks

Inside notebooks, you'll find path_gen folder, it contains a single jupyter notebook, alongside the data used to run it.

This is a detailed-ish code from Binh to develop the 3D triangulation pipeline. It contains everything from sfm sparse reconstruction to how to map local world coords to ecef.
