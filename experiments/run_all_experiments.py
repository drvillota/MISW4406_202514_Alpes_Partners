"""
Ejecutor de Experimentos - Patrón Saga
Script principal para ejecutar todos los experimentos de calidad
"""
import asyncio
import json
from datetime import datetime, timezone
from performance_experiment import PerformanceExperiment
from resilience_experiment import ResilienceExperiment
from observability_experiment import ObservabilityExperiment

async def run_all_experiments():
    """Ejecutar todos los experimentos en secuencia"""
    print("SUITE COMPLETA DE EXPERIMENTOS - PATRÓN SAGA")
    print("=" * 70)
    print("Este script ejecutará los siguientes experimentos:")
    print("1. Rendimiento: Throughput y latencia bajo carga")
    print("2. Resiliencia: Manejo de fallos y compensaciones")
    print("3. Observabilidad: Trazabilidad y consultas rápidas")
    print()
    
    # Confirmar ejecución
    print("NOTA: Asegúrate de que el BFF esté ejecutándose en http://localhost:8000")
    response = input("¿Deseas continuar? (y/N): ").strip().lower()
    if response != 'y':
        print("Ejecución cancelada")
        return
    
    results_summary = {
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "experiments": {}
    }
    
    # Experimento 1: Rendimiento
    print("\n" + "="*70)
    print("EJECUTANDO EXPERIMENTO DE RENDIMIENTO")
    print("="*70)
    try:
        performance_exp = PerformanceExperiment()
        performance_results = await performance_exp.run_performance_test()
        results_summary["experiments"]["performance"] = {
            "status": performance_results.get("status"),
            "hypothesis_met": performance_results.get("conclusion", {}).get("hypothesis_met"),
            "summary": performance_results.get("conclusion", {}).get("summary"),
            "key_metrics": {
                "throughput_rps": performance_results.get("results", {}).get("throughput_requests_per_second"),
                "p95_latency_ms": performance_results.get("results", {}).get("latency_stats", {}).get("p95_ms"),
                "success_rate": performance_results.get("results", {}).get("success_rate")
            }
        }
        print("Experimento de rendimiento completado")
    except Exception as e:
        print(f"Error en experimento de rendimiento: {e}")
        results_summary["experiments"]["performance"] = {"status": "FAILED", "error": str(e)}
    
    # Pausa entre experimentos
    print("\nPausa de 30 segundos antes del siguiente experimento...")
    await asyncio.sleep(30)
    
    # Experimento 2: Resiliencia
    print("\n" + "="*70)
    print("EJECUTANDO EXPERIMENTO DE RESILIENCIA")
    print("="*70)
    try:
        resilience_exp = ResilienceExperiment()
        resilience_results = await resilience_exp.run_resilience_test()
        results_summary["experiments"]["resilience"] = {
            "status": resilience_results.get("status"),
            "hypothesis_met": resilience_results.get("conclusion", {}).get("hypothesis_met"),
            "summary": resilience_results.get("conclusion", {}).get("summary"),
            "key_metrics": {
                "resilience_score": resilience_results.get("results", {}).get("overall_resilience", {}).get("resilience_score"),
                "normal_success_rate": resilience_results.get("results", {}).get("normal_scenarios_analysis", {}).get("success_rate"),
                "failure_recovery_rate": resilience_results.get("results", {}).get("failing_scenarios_analysis", {}).get("recovery_rate")
            }
        }
        print("Experimento de resiliencia completado")
    except Exception as e:
        print(f"Error en experimento de resiliencia: {e}")
        results_summary["experiments"]["resilience"] = {"status": "FAILED", "error": str(e)}
    
    # Pausa entre experimentos
    print("\nPausa de 30 segundos antes del siguiente experimento...")
    await asyncio.sleep(30)
    
    # Experimento 3: Observabilidad
    print("\n" + "="*70)
    print("EJECUTANDO EXPERIMENTO DE OBSERVABILIDAD")
    print("="*70)
    try:
        observability_exp = ObservabilityExperiment()
        observability_results = await observability_exp.run_observability_test()
        results_summary["experiments"]["observability"] = {
            "status": observability_results.get("status"),
            "hypothesis_met": observability_results.get("conclusion", {}).get("hypothesis_met"),
            "summary": observability_results.get("conclusion", {}).get("summary"),
            "key_metrics": {
                "avg_query_time_ms": observability_results.get("results", {}).get("individual_queries", {}).get("avg_query_time_ms"),
                "traceability_rate": observability_results.get("results", {}).get("traceability", {}).get("traceability_rate"),
                "query_success_rate": observability_results.get("results", {}).get("individual_queries", {}).get("success_rate")
            }
        }
        print("Experimento de observabilidad completado")
    except Exception as e:
        print(f"Error en experimento de observabilidad: {e}")
        results_summary["experiments"]["observability"] = {"status": "FAILED", "error": str(e)}
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL DE EXPERIMENTOS")
    print("="*70)
    
    overall_success = True
    for exp_name, exp_data in results_summary["experiments"].items():
        status = exp_data.get("status", "UNKNOWN")
        hypothesis_met = exp_data.get("hypothesis_met", False)
        
        if status != "COMPLETED" or not hypothesis_met:
            overall_success = False
        
        print(f"\n🔬 {exp_name.upper()}")
        print(f"   Status: {status}")
        if "summary" in exp_data:
            print(f"   {exp_data['summary']}")
        if "key_metrics" in exp_data:
            print(f"   Métricas clave: {exp_data['key_metrics']}")
    
    results_summary["overall_success"] = overall_success
    results_summary["conclusion"] = (
        "TODOS LOS EXPERIMENTOS EXITOSOS: El patrón saga cumple con los requisitos de calidad" 
        if overall_success else 
        "⚠️ ALGUNOS EXPERIMENTOS FALLARON: Revisar resultados detallados para optimizaciones"
    )
    
    # Guardar resumen consolidado
    with open("experiments_summary.json", "w") as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\nCONCLUSIÓN GENERAL")
    print("="*30)
    print(results_summary["conclusion"])
    print(f"\nResumen consolidado guardado en: experiments_summary.json")
    
    return results_summary

def print_instructions():
    """Mostrar instrucciones para ejecutar experimentos individuales"""
    print("""
INSTRUCCIONES PARA EXPERIMENTOS INDIVIDUALES

Para ejecutar experimentos por separado:

1. Experimento de Rendimiento:
   python performance_experiment.py

2. Experimento de Resiliencia:
   python resilience_experiment.py

3. Experimento de Observabilidad:
   python observability_experiment.py

PREREQUISITOS:
- BFF Service ejecutándose en http://localhost:8000
- Instalar dependencias: pip install aiohttp asyncio
- Docker containers activos (usar docker-compose up)

ARCHIVOS DE SALIDA:
- performance_experiment_results.json
- resilience_experiment_results.json  
- observability_experiment_results.json
- experiments_summary.json (este script)
""")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_instructions()
    else:
        asyncio.run(run_all_experiments())