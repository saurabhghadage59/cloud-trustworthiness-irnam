"""Provider collector registry."""

from dataset_builder.collectors.aws import AWSCollector
from dataset_builder.collectors.azure import AzureCollector
from dataset_builder.collectors.gcp import GCPCollector
from dataset_builder.collectors.ibm import IBMCollector
from dataset_builder.collectors.oracle import OracleCollector

COLLECTORS = (AWSCollector, AzureCollector, GCPCollector, OracleCollector, IBMCollector)

__all__ = ["AWSCollector", "AzureCollector", "GCPCollector", "OracleCollector", "IBMCollector", "COLLECTORS"]
