#built-in modules
import datetime
import os

#third-party libraries
from azure.ai.ml import MLClient
from azure.ai.ml.entities import ComputeInstance, AmlCompute
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient 
from azure.mgmt.compute.models import RunCommandInput
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from dotenv import load_dotenv
import paramiko
import requests

# Load the .env file
load_dotenv()

#own libraries


# Access the variables 
subscription_id_env = os.getenv('subscription_id')


def AML_workspace(subscription_id, resource_group, workspace):
    # Enter details of your AML workspace
    # subscription_id = f"<SUBSCRIPTION_ID>"
    # resource_group = f"<RESOURCE_GROUP>"
    # workspace = f"<AML_WORKSPACE_NAME>"

    ml_client = MLClient(
        DefaultAzureCredential(), subscription_id, resource_group, workspace
    )

    return ml_client


def list_azure_compute_instances(subscription_id):
    """
    List all Azure compute instances in a subscription.

    Args:
        subscription_id (str): Azure subscription ID.

    Returns:
        list: A list of compute instance names and details.
    """
    try:
        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create ComputeManagementClient
        compute_client = ComputeManagementClient(credential, subscription_id)

        # List all virtual machines in the subscription
        vms = compute_client.virtual_machines.list_all()

        # Collect instance details
        compute_instances = []
        for vm in vms:
            instance_info = {
                "name": vm.name,
                "location": vm.location,
                "resource_group": vm.id.split("/")[4],
            }
            compute_instances.append(instance_info)

        return compute_instances

    except Exception as e:
        print(f"Error: {e}")
        return []


def list_dedicated_cores(subscription_id, location):
    """
    Lists dedicated cores (quota limits) available for the subscription in a specific location.

    Args:
        subscription_id (str): Azure subscription ID.
        location (str): Azure location (e.g., 'eastus').

    Returns:
        dict: A dictionary containing dedicated core limits and usage.
    """
    try:
        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create ComputeManagementClient
        compute_client = ComputeManagementClient(credential, subscription_id)

        # Fetch usage details for the specified location
        usage_details = compute_client.usage.list(location)

        # Parse the usage details
        dedicated_cores = {}
        for item in usage_details:
            if "cores" in item.name.value.lower():  # Filter for core-related items
                dedicated_cores[item.name.localized_value] = {
                    "current_usage": item.current_value,
                    "limit": item.limit,
                }

        return dedicated_cores

    except Exception as e:
        print(f"Error: {e}")
        return {}


def list_available_vm_sizes(subscription_id, location):
    """
    Lists the specific Azure VM sizes available for a subscription in a given location.

    Args:
        subscription_id (str): Azure subscription ID.
        location (str): Azure location (e.g., 'eastus').

    Returns:
        list: A list of VM size details available in the specified location.
    """
    try:
        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create ComputeManagementClient
        compute_client = ComputeManagementClient(credential, subscription_id)

        # Get available VM sizes for the specified location
        vm_sizes = compute_client.virtual_machine_sizes.list(location)

        # Format the VM size details
        available_vm_sizes = []
        for vm_size in vm_sizes:
            vm_info = {
                "name": vm_size.name,
                "number_of_cores": vm_size.number_of_cores,
                "memory_in_mb": vm_size.memory_in_mb,
                "max_data_disk_count": vm_size.max_data_disk_count
            }
            available_vm_sizes.append(vm_info)

        return available_vm_sizes

    except Exception as e:
        print(f"Error: {e}")
        return []    


def create_vm(size = None):
    # Enter details of your AML workspace
    subscription_id = subscription_id_env
    resource_group = "lawgorithm_group"
    workspace = "Lawgorithm2"
    # size = 'Standard_NC8as_T4_v3'

    ml_client = AML_workspace(subscription_id=subscription_id, 
                              resource_group=resource_group, 
                              workspace=workspace)

    vm_name = "basic-ci" + datetime.date.today().strftime("%Y%m%d%H%M")

    if size!=None:
        vm = ComputeInstance(name=vm_name, size=size)
    else: 
        vm = ComputeInstance(name=vm_name)

    ml_client.begin_create_or_update(vm).result()
    print('VM created')
    return vm_name


def delete_vm(vm_name: str):   
    # Enter details of your AML workspace
    subscription_id = subscription_id_env
    resource_group = "lawgorithm_group"
    workspace = "Lawgorithm2"
    size = 'Standard_NC8as_T4_v3'

    ml_client = AML_workspace(subscription_id=subscription_id, 
                              resource_group=resource_group, 
                              workspace=workspace)

    # vm_name = "basic-ci" + datetime.datetime.now().strftime("%Y%m%d%H%M")
    ml_client.compute.begin_delete(vm_name).wait()

    print('VM deleted')


def is_azure_vm():
    try:
        # Query the Azure Metadata Service
        url = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
        headers = {"Metadata": "true"}
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            # Successfully accessed the metadata service
            metadata = response.json()
            return True, metadata
        else:
            return False, None
    except requests.exceptions.RequestException:
        # Unable to reach the metadata service
        return False, None
    

def check_azure_vm():
    try:
        credential = DefaultAzureCredential()
        # This will only work if running in an Azure environment with proper credentials
        return True
    except:
        return False
    

def main0():
    # Enter details of your AML workspace
    subscription_id = subscription_id_env
    resource_group = "lawgorithm_group"
    workspace = "Lawgorithm2"
    size = 'Standard_NC8as_T4_v3'

    ml_client = AML_workspace(subscription_id=subscription_id, 
                              resource_group=resource_group, 
                              workspace=workspace)

    vm_name = "basic-ci" + datetime.datetime.now().strftime("%Y%m%d%H%M")

    vm = ComputeInstance(name=vm_name, size=size)
    ml_client.begin_create_or_update(vm).result()
    print('VM created')
    vm_state = ml_client.compute.get(vm_name)
    print(vm_state)

    ml_client.compute.begin_delete(vm_name).wait()

    print('VM deleted')


def main1():
    subscription_id = subscription_id_env  # Replace with your subscription ID
    instances = list_azure_compute_instances(subscription_id)
    if instances:
        for idx, instance in enumerate(instances, start=1):
            print(f"{idx}. Name: {instance['name']}, Location: {instance['location']}, Resource Group: {instance['resource_group']}")
    else:
        print("No compute instances found or an error occurred.")


def main2():
    subscription_id = subscription_id_env  # Replace with your subscription ID
    location = "westus3"  # Replace with your desired Azure location
    dedicated_cores = list_dedicated_cores(subscription_id, location)

    if dedicated_cores:
        print(f"Dedicated cores in location {location}:")
        for core_type, details in dedicated_cores.items():
            print(f"  {core_type}: Used {details['current_usage']} / {details['limit']}")
    else:
        print("No dedicated core information found or an error occurred.")


def main3():
    subscription_id = subscription_id_env  # Replace with your subscription ID
    location = "westus2"  # Replace with your desired Azure location
    vm_sizes = list_available_vm_sizes(subscription_id, location)

    if vm_sizes:
        print(f"Available VM sizes in {location}:")
        for vm in vm_sizes:
            print(f"  Name: {vm['name']}, Cores: {vm['number_of_cores']}, Memory: {vm['memory_in_mb']} MB, Max Disks: {vm['max_data_disk_count']}")
    else:
        print("No VM sizes found or an error occurred.")    


def main4():
    var = subscription_id_env
    print(var)


def main5():
    vm_name = create_vm()

    # # Check if running on Azure VM
    # is_vm, metadata = is_azure_vm()
    # if is_vm:
    #     print("This code is running on an Azure VM.")
    #     print("Metadata:", metadata)
    # else:
    #     print("This code is NOT running on an Azure VM.")

    delete_vm(vm_name=vm_name)


def main6():
    # Replace with your subscription ID and VM details
    subscription_id = "your-subscription-id"
    resource_group_name = "your-resource-group-name"
    vm_name = "your-vm-name"

    # Authenticate
    credential = DefaultAzureCredential()
    compute_client = ComputeManagementClient(credential, subscription_id)

    # Get the VM details
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type

    print(f"The OS type of the VM is: {os_type}")   


def main7():
    # Authenticate using DefaultAzureCredential
    credential = DefaultAzureCredential()
    # vm_name = create_vm()

    # Initialize the ComputeManagementClient
    compute_client = ComputeManagementClient(credential, subscription_id_env)

    # Replace with your resource group and VM name
    resource_group = 'Lawgorithm_group'
    
    # Initialize the ResourceManagementClient
    resource_client = ResourceManagementClient(credential, subscription_id_env)

    # List all resource groups
    resource_groups = resource_client.resource_groups.list()

    print("Resource Groups:")
    for rg in resource_groups:
        print(f"- Name: {rg.name}, Location: {rg.location}")

    # List VMs in the specified resource group
    vms = compute_client.virtual_machines.list(resource_group)
    print("VMs in Resource Group:")
    for vm in vms:
        print(f"- {vm.name}")
        print(f"VM Details: {vm}")

    # Initialize the NetworkManagementClient
    network_client = NetworkManagementClient(credential, subscription_id_env)

    # List all public IP addresses in the resource group
    public_ips = network_client.public_ip_addresses.list(resource_group)

    print("Public IP Addresses:")
    for ip in public_ips:
        print(f"Name: {ip.name}, IP Address: {ip.ip_address}")

    # Replace with your public IP resource group and name
    ip_name = 'prueba-ip'
    public_ip = network_client.public_ip_addresses.get(resource_group, ip_name).ip_address
    print(f"VM Public IP: {public_ip}")

    # # Replace with your VM's credentials
    # username = 'prueba'
    # private_key_path = r"C:\Users\Andres.DESKTOP-D77KM25\Downloads\prueba_key.pem"

    # # Initialize SSH client
    # ssh_client = paramiko.SSHClient()
    # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # # Connect to the VM
    # ssh_client.connect(hostname=public_ip, username=username, key_filename=private_key_path)

    # # Execute a command
    # stdin, stdout, stderr = ssh_client.exec_command('ls -al')
    # print(stdout.read().decode())
    # ssh_client.close()

    # Get VM details
    # vm = compute_client.virtual_machines.get(resource_group, vm_name)
    
    # delete_vm(vm_name=vm_name)


def main8():
    # Replace with your resource group and VM name
    resource_group = 'Lawgorithm_group'
    # Initialize the NetworkManagementClient
    network_client = NetworkManagementClient(DefaultAzureCredential(), subscription_id_env)

    # Replace with your public IP resource group and name
    ip_name = 'prueba-ip'
    public_ip = network_client.public_ip_addresses.get(resource_group, ip_name).ip_address
    print(f"VM Public IP: {public_ip}")

    # Replace with your VM's credentials
    username = 'azureuser'
    ssh_private_key_path = r"C:\Users\Andres.DESKTOP-D77KM25\Downloads\prueba_key.pem"

    # Initialize SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load private key
    private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key_path)
    
    print('private_key: ', private_key)

    # Connect to VM
    print(f"Connecting to {public_ip}...")
    ssh_client.connect(
        hostname=public_ip,
        username=username,
        pkey=private_key
    )

    # Connect to the VM
    # ssh_client.connect(hostname=public_ip, username=username, key_filename=private_key_path)

    # Execute a command
    stdin, stdout, stderr = ssh_client.exec_command('ls -al')
    print(stdout.read().decode())

    # Upload the script to the VM
    sftp = ssh_client.open_sftp()
    sftp.put('test_script.py', f'/home/{username}/remote_script.py')
    sftp.close()

    # Run the script
    stdin, stdout, stderr = ssh_client.exec_command(f'python3 /home/{username}/remote_script.py')
    print(stdout.read().decode())


def main9():
    # Authenticate with Azure
    credential = DefaultAzureCredential()

    # Replace with your Azure subscription ID
    subscription_id = subscription_id_env

    # Initialize ComputeManagementClient
    compute_client = ComputeManagementClient(credential, subscription_id)

    # Define the Python script as a string
    python_script = """
#!/usr/bin/env python3
import os
hello = "hola"
print('hello')
    """

    # Define the Run Command input
    command = RunCommandInput(
        command_id="RunShellScript",  # Use "RunPowerShellScript" for Windows
        script=[
            "echo '{}' > /tmp/custom_script.py".format(python_script.replace("\n", "\\n")),  # Upload the script
            "python3 /tmp/custom_script.py"  # Run the script
        ]
    )
    # Replace with your resource group and VM name
    resource_group = 'Lawgorithm_group'
    vm_name = 'prueba'

    # Execute the Run Command
    response = compute_client.virtual_machines.begin_run_command(
        resource_group_name=resource_group,
        vm_name=vm_name,
        parameters=command
    )

    # Wait for the command to complete and get the result
    result = response.result()
    print("Run Command Output:")
    for message in result.value:
        print(message.message)



if __name__ == '__main__':
    main9()


