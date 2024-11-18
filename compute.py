# import required libraries
from azure.ai.ml import MLClient
from azure.ai.ml.entities import ComputeInstance, AmlCompute
from azure.identity import DefaultAzureCredential
import datetime
from azure.mgmt.compute import ComputeManagementClient


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



def main0():
    # Enter details of your AML workspace
    subscription_id = "ae1f30fd-b0e1-4fff-b4a6-e80db7622ce1"
    resource_group = "lawgorithm_group"
    workspace = "Lawgorithm"

    ml_client = AML_workspace(subscription_id=subscription_id, 
                              resource_group=resource_group, 
                              workspace=workspace)

    ci_basic_name = "basic-ci" + datetime.datetime.now().strftime("%Y%m%d%H%M")

    ci_basic = ComputeInstance(name=ci_basic_name, size="STANDARD_NC8AS_T4_V3")
    ml_client.begin_create_or_update(ci_basic).result()
    print('VM created')
    ci_basic_state = ml_client.compute.get(ci_basic_name)
    print(ci_basic_state)

    ml_client.compute.begin_delete(ci_basic_name).wait()

    print('VM deleted')


if __name__ == '__main__':
    subscription_id = "ae1f30fd-b0e1-4fff-b4a6-e80db7622ce1"  # Replace with your subscription ID
    instances = list_azure_compute_instances(subscription_id)
    if instances:
        for idx, instance in enumerate(instances, start=1):
            print(f"{idx}. Name: {instance['name']}, Location: {instance['location']}, Resource Group: {instance['resource_group']}")
    else:
        print("No compute instances found or an error occurred.")



