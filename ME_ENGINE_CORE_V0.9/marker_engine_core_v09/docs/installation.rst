Installation
============

System Requirements
-------------------

- Python 3.9 or higher
- pip package manager
- Git (for cloning the repository)

Installation from Source
------------------------

1. Clone the repository:

   .. code-block:: bash

      git clone <repository-url>
      cd marker-engine

2. Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

3. (Optional) Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

Installation via pip
--------------------

.. code-block:: bash

   pip install marker-engine

Docker Installation
-------------------

1. Build the Docker image:

   .. code-block:: bash

      docker build -t marker-engine .

2. Run the container:

   .. code-block:: bash

      docker run -p 8000:8000 marker-engine

Docker Compose
--------------

1. Start all services:

   .. code-block:: bash

      docker-compose up -d

2. Access the API at http://localhost:80

Verification
------------

After installation, verify the setup:

.. code-block:: bash

   python -c "import marker_engine_core; print('Installation successful!')"

Run the validation script:

.. code-block:: bash

   python validate_system.py
