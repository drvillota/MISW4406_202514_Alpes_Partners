"""
Experimento de Observabilidad - Saga Pattern
Valida que el saga log permite trazabilidad completa y consultas rápidas
"""
import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

# Configuración del experimento
BFF_BASE_URL = "http://localhost:8000"
TEST_SAGAS_COUNT = 15
QUERY_TEST_ITERATIONS = 50

class ObservabilityExperiment:
    def __init__(self):
        self.created_sagas = []
        self.query_results = []
        
    async def create_test_sagas(self, session: aiohttp.ClientSession) -> List[str]:
        """Crear sagas de prueba para experimentos de observabilidad"""
        print(f"Creando {TEST_SAGAS_COUNT} sagas de prueba...")
        
        saga_ids = []
        
        for i in range(TEST_SAGAS_COUNT):
            payload = {
                "affiliate_name": f"Observability Test User {i}",
                "affiliate_email": f"obs.test.{i}@example.com",
                "commission_rate": 0.15,
                "content_type": "BLOG",
                "content_title": f"Observability Test Content {i}",
                "content_description": f"Test content for observability experiment {i}",
                "collaboration_type": "CONTENT_CREATION"
            }
            
            try:
                async with session.post(
                    f"{BFF_BASE_URL}/api/v1/sagas/complete-affiliate-registration",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        saga_id = data.get("saga_id")
                        saga_ids.append(saga_id)
                        print(f"   ✓ Saga {i+1} creada: {saga_id}")
                    else:
                        print(f"   Error creando saga {i+1}: HTTP {response.status}")
            except Exception as e:
                print(f"   Error creando saga {i+1}: {e}")
            
            # Pausa para no sobrecargar
            await asyncio.sleep(0.5)
        
        return saga_ids
    
    async def test_individual_saga_query(self, session: aiohttp.ClientSession, saga_id: str) -> Dict[str, Any]:
        """Probar consulta individual de saga"""
        start_time = time.time()
        
        try:
            async with session.get(
                f"{BFF_BASE_URL}/api/v1/sagas/{saga_id}/status",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                end_time = time.time()
                query_time = (end_time - start_time) * 1000  # ms
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "saga_id": saga_id,
                        "query_time_ms": query_time,
                        "success": True,
                        "status": data.get("status"),
                        "steps_count": len(data.get("steps", [])),
                        "has_detailed_steps": len(data.get("steps", [])) > 0,
                        "complete_traceability": self.validate_traceability(data)
                    }
                else:
                    return {
                        "saga_id": saga_id,
                        "query_time_ms": query_time,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            end_time = time.time()
            query_time = (end_time - start_time) * 1000
            return {
                "saga_id": saga_id,
                "query_time_ms": query_time,
                "success": False,
                "error": str(e)
            }
    
    def validate_traceability(self, saga_data: Dict[str, Any]) -> bool:
        """Validar que la saga tiene trazabilidad completa"""
        steps = saga_data.get("steps", [])
        
        # Verificar que cada step tiene los campos necesarios
        required_fields = ["step_name", "status", "timestamp", "payload"]
        
        for step in steps:
            for field in required_fields:
                if field not in step:
                    return False
        
        # Verificar orden cronológico
        if len(steps) > 1:
            for i in range(1, len(steps)):
                prev_time = datetime.fromisoformat(steps[i-1]["timestamp"].replace("Z", "+00:00"))
                curr_time = datetime.fromisoformat(steps[i]["timestamp"].replace("Z", "+00:00"))
                if curr_time < prev_time:
                    return False
        
        return True
    
    async def test_list_sagas_query(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Probar consulta de listado de sagas"""
        start_time = time.time()
        
        try:
            async with session.get(
                f"{BFF_BASE_URL}/api/v1/sagas?limit=50",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                end_time = time.time()
                query_time = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    sagas = data.get("sagas", [])
                    
                    return {
                        "query_type": "list_sagas",
                        "query_time_ms": query_time,
                        "success": True,
                        "total_sagas": len(sagas),
                        "has_pagination": "total" in data,
                        "has_filters": "filters" in data
                    }
                else:
                    return {
                        "query_type": "list_sagas",
                        "query_time_ms": query_time,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            end_time = time.time()
            query_time = (end_time - start_time) * 1000
            return {
                "query_type": "list_sagas",
                "query_time_ms": query_time,
                "success": False,
                "error": str(e)
            }
    
    async def test_statistics_query(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Probar consulta de estadísticas"""
        start_time = time.time()
        
        try:
            async with session.get(
                f"{BFF_BASE_URL}/api/v1/sagas/statistics",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                end_time = time.time()
                query_time = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "query_type": "statistics",
                        "query_time_ms": query_time,
                        "success": True,
                        "has_total_count": "total_sagas" in data,
                        "has_status_breakdown": "by_status" in data,
                        "has_type_breakdown": "by_type" in data,
                        "statistics_complete": all(key in data for key in ["total_sagas", "by_status", "by_type"])
                    }
                else:
                    return {
                        "query_type": "statistics",
                        "query_time_ms": query_time,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            end_time = time.time()
            query_time = (end_time - start_time) * 1000
            return {
                "query_type": "statistics",
                "query_time_ms": query_time,
                "success": False,
                "error": str(e)
            }
    
    async def run_query_performance_tests(self, session: aiohttp.ClientSession, saga_ids: List[str]) -> List[Dict[str, Any]]:
        """Ejecutar pruebas de rendimiento de consultas"""
        print(f"🔍 Ejecutando {QUERY_TEST_ITERATIONS} consultas de rendimiento...")
        
        query_results = []
        
        for i in range(QUERY_TEST_ITERATIONS):
            # Elegir saga aleatoria para consultar
            import random
            saga_id = random.choice(saga_ids) if saga_ids else None
            
            if saga_id:
                # Test consulta individual
                individual_result = await self.test_individual_saga_query(session, saga_id)
                individual_result["iteration"] = i
                individual_result["query_type"] = "individual"
                query_results.append(individual_result)
            
            # Test consulta de listado (cada 5 iteraciones)
            if i % 5 == 0:
                list_result = await self.test_list_sagas_query(session)
                list_result["iteration"] = i
                query_results.append(list_result)
            
            # Test consulta de estadísticas (cada 10 iteraciones)
            if i % 10 == 0:
                stats_result = await self.test_statistics_query(session)
                stats_result["iteration"] = i
                query_results.append(stats_result)
            
            # Pausa pequeña entre consultas
            await asyncio.sleep(0.1)
        
        return query_results
    
    async def run_observability_test(self) -> Dict[str, Any]:
        """Ejecutar el experimento completo de observabilidad"""
        print("Iniciando Experimento de Observabilidad de Saga...")
        print(f"   - Sagas de prueba: {TEST_SAGAS_COUNT}")
        print(f"   - Iteraciones de consulta: {QUERY_TEST_ITERATIONS}")
        
        async with aiohttp.ClientSession() as session:
            # Fase 1: Crear sagas de prueba
            saga_ids = await self.create_test_sagas(session)
            
            # Esperar a que se procesen las sagas
            print("Esperando que las sagas se procesen...")
            await asyncio.sleep(10)
            
            # Fase 2: Ejecutar tests de rendimiento de consultas
            query_results = await self.run_query_performance_tests(session, saga_ids)
        
        return self.analyze_observability_results(saga_ids, query_results)
    
    def analyze_observability_results(self, saga_ids: List[str], query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar resultados del experimento de observabilidad"""
        # Separar resultados por tipo de consulta
        individual_queries = [r for r in query_results if r.get("query_type") == "individual"]
        list_queries = [r for r in query_results if r.get("query_type") == "list_sagas"]
        stats_queries = [r for r in query_results if r.get("query_type") == "statistics"]
        
        # Análisis de consultas individuales
        successful_individual = [r for r in individual_queries if r.get("success", False)]
        individual_times = [r["query_time_ms"] for r in successful_individual]
        
        # Análisis de trazabilidad
        traceable_sagas = [r for r in successful_individual if r.get("complete_traceability", False)]
        
        # Análisis de consultas de listado
        successful_list = [r for r in list_queries if r.get("success", False)]
        list_times = [r["query_time_ms"] for r in successful_list]
        
        # Análisis de estadísticas
        successful_stats = [r for r in stats_queries if r.get("success", False)]
        stats_times = [r["query_time_ms"] for r in successful_stats]
        
        analysis = {
            "experiment_type": "observability",
            "status": "COMPLETED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "configuration": {
                "test_sagas_count": TEST_SAGAS_COUNT,
                "query_test_iterations": QUERY_TEST_ITERATIONS,
                "created_sagas": len(saga_ids)
            },
            "results": {
                "saga_creation": {
                    "attempted": TEST_SAGAS_COUNT,
                    "successful": len(saga_ids),
                    "success_rate": round(len(saga_ids) / TEST_SAGAS_COUNT * 100, 2)
                },
                "individual_queries": {
                    "total_queries": len(individual_queries),
                    "successful": len(successful_individual),
                    "success_rate": round(len(successful_individual) / len(individual_queries) * 100, 2) if individual_queries else 0,
                    "avg_query_time_ms": round(statistics.mean(individual_times), 2) if individual_times else 0,
                    "median_query_time_ms": round(statistics.median(individual_times), 2) if individual_times else 0,
                    "max_query_time_ms": round(max(individual_times), 2) if individual_times else 0
                },
                "traceability": {
                    "total_traced": len(traceable_sagas),
                    "traceability_rate": round(len(traceable_sagas) / len(successful_individual) * 100, 2) if successful_individual else 0
                },
                "list_queries": {
                    "total_queries": len(list_queries),
                    "successful": len(successful_list),
                    "avg_query_time_ms": round(statistics.mean(list_times), 2) if list_times else 0
                },
                "statistics_queries": {
                    "total_queries": len(stats_queries),
                    "successful": len(successful_stats),
                    "avg_query_time_ms": round(statistics.mean(stats_times), 2) if stats_times else 0
                }
            },
            "hypothesis_validation": {
                "expected_query_time_max": 1000,  # ms
                "expected_traceability_rate": 95,  # %
                "expected_query_success_rate": 98,  # %
                "actual_avg_query_time": round(statistics.mean(individual_times), 2) if individual_times else 0,
                "actual_traceability_rate": round(len(traceable_sagas) / len(successful_individual) * 100, 2) if successful_individual else 0,
                "actual_query_success_rate": round(len(successful_individual) / len(individual_queries) * 100, 2) if individual_queries else 0,
                "query_time_met": (statistics.mean(individual_times) <= 1000) if individual_times else False,
                "traceability_met": (len(traceable_sagas) / len(successful_individual) * 100) >= 95 if successful_individual else False,
                "success_rate_met": (len(successful_individual) / len(individual_queries) * 100) >= 98 if individual_queries else False
            }
        }
        
        # Verificar si se cumple la hipótesis
        hypothesis_met = (analysis["hypothesis_validation"]["query_time_met"] and 
                         analysis["hypothesis_validation"]["traceability_met"] and 
                         analysis["hypothesis_validation"]["success_rate_met"])
        
        analysis["conclusion"] = {
            "hypothesis_met": hypothesis_met,
            "summary": self.generate_observability_summary(analysis)
        }
        
        return analysis
    
    def generate_observability_summary(self, analysis: Dict[str, Any]) -> str:
        """Generar resumen de conclusiones de observabilidad"""
        results = analysis["results"]
        hypothesis = analysis["hypothesis_validation"]
        
        if analysis["conclusion"]["hypothesis_met"]:
            return (f"HIPÓTESIS CUMPLIDA: Sistema observable con "
                   f"{results['individual_queries']['avg_query_time_ms']}ms tiempo promedio de consulta, "
                   f"{results['traceability']['traceability_rate']}% trazabilidad completa, "
                   f"{results['individual_queries']['success_rate']}% tasa de éxito en consultas")
        else:
            issues = []
            if not hypothesis["query_time_met"]:
                issues.append(f"consultas lentas ({hypothesis['actual_avg_query_time']}ms > 1000ms)")
            if not hypothesis["traceability_met"]:
                issues.append(f"baja trazabilidad ({hypothesis['actual_traceability_rate']}% < 95%)")
            if not hypothesis["success_rate_met"]:
                issues.append(f"baja tasa de éxito ({hypothesis['actual_query_success_rate']}% < 98%)")
            
            return f"HIPÓTESIS NO CUMPLIDA: {', '.join(issues)}"

async def main():
    experiment = ObservabilityExperiment()
    
    print("🔬 EXPERIMENTO DE OBSERVABILIDAD - PATRÓN SAGA")
    print("=" * 60)
    
    try:
        results = await experiment.run_observability_test()
        
        # Guardar resultados
        with open("observability_experiment_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Mostrar resumen
        print("\nRESULTADOS DEL EXPERIMENTO")
        print("=" * 40)
        print(f"Status: {results['status']}")
        print(f"Sagas creadas: {results['results']['saga_creation']['successful']}/{results['results']['saga_creation']['attempted']}")
        print(f"Consultas individuales exitosas: {results['results']['individual_queries']['successful']}/{results['results']['individual_queries']['total_queries']}")
        print(f"Tiempo promedio de consulta: {results['results']['individual_queries']['avg_query_time_ms']}ms")
        print(f"Trazabilidad completa: {results['results']['traceability']['traceability_rate']}%")
        print()
        print("VALIDACIÓN DE HIPÓTESIS")
        print("=" * 30)
        print(results['conclusion']['summary'])
        
        print("\nResultados guardados en: observability_experiment_results.json")
        
    except Exception as e:
        print(f"Error en experimento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())