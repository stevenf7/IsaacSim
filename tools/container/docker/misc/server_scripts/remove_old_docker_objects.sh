SCRIPT_PATH=$(dirname `readlink -f $0`) 
cd $SCRIPT_PATH
python3.6 remove_old_docker_objects.py
