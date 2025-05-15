# Policy Whisperer

A prompt-based interaction system for generating CyberArk Conjur policies based on user intentions.

## Overview

Policy Whisperer helps you generate Conjur policies through natural language prompts. It uses templates from the [conjur-policies](https://github.com/infamousjoeg/conjur-policies) repository and allows users to state their intentions in plain language to get policy suggestions.

## Features

- Natural language interaction for policy generation
- Based on real-world Conjur policy templates
- Supports various policy types (authentication, cloud, CI/CD, etc.)
- Generates YAML-formatted policies ready for use with Conjur

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Follow the prompts to generate your Conjur policy.

## Requirements

- Python 3.8+
- Required packages listed in requirements.txt
